import unittest
import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime
from frequency_utils import calculate_word_trends, detect_burst_words
from history_queue import HistoryDataQueue
import numpy as np

# 假设你的函数在一个名为 frequency_utils 的文件中
from frequency_utils import calculate_word_trends, detect_burst_words


# ========================================================
# 测试辅助类：模拟 HistoryDataQueue
# ========================================================
class MockHistoryQueue:
    """模拟你的 HistoryDataQueue 类，只实现 get_all 用于测试"""
    def __init__(self, data_list):
        # data_list 格式: [(timestamp, df), (timestamp, df), ...]
        self.data = data_list

    def get_all(self):
        return self.data

# ========================================================
# 单元测试类
# ========================================================
class TestTrendAnalysis(unittest.TestCase):

    def setUp(self):
        # print("\n--- Setting up test data ---")
        pass

    # ------------------------------------------------
    # 测试 calculate_word_trends
    # ------------------------------------------------
    def test_calculate_word_trends(self):
        print("\n🧪 Testing calculate_word_trends...")

        # 1. 构造旧数据 (Round 1)
        old_data = pd.DataFrame({
            'word': ['apple', 'banana', 'common_word'],
            'count': [10, 5, 20]
        })

        # 2. 构造新数据 (Round 2)
        # - apple: 消失 (Lost)
        # - banana: 依然存在 (Common)
        # - common_word: 频率变大 (Common)
        # - durian: 新出现 (New)
        new_data = pd.DataFrame({
            'word': ['banana', 'common_word', 'durian'],
            'count': [5, 50, 15]
        })

        # 3. 运行函数
        result = calculate_word_trends(old_data, new_data)

        # 4. 验证 'new' (New words)
        new_df = result['new']
        print(f"  [New Words]: found {len(new_df)}")
        self.assertEqual(len(new_df), 1)
        self.assertEqual(new_df.iloc[0]['word'], 'durian')
        self.assertEqual(new_df.iloc[0]['trend'], 'new')

        # 5. 验证 'lost' (Lost words)
        lost_df = result['lost']
        print(f"  [Lost Words]: found {len(lost_df)}")
        self.assertEqual(len(lost_df), 1)
        self.assertEqual(lost_df.iloc[0]['word'], 'apple')
        self.assertEqual(lost_df.iloc[0]['trend'], 'lost')

        # 6. 验证 'common' (Common words)
        common_df = result['common']
        print(f"  [Common Words]: found {len(common_df)}")
        self.assertEqual(len(common_df), 2) # banana, common_word
        
        # 验证 growth rate calculation
        # common_word: old=20, new=50 -> change=30 -> rate=1.5
        word_row = common_df[common_df['word'] == 'common_word'].iloc[0]
        self.assertAlmostEqual(word_row['freq_change_rate'], 1.5)
        print("  ✅ calculate_word_trends Passed!")

    # ------------------------------------------------
    # 测试 detect_burst_words
    # ------------------------------------------------
    def test_detect_burst_words(self):
        print("\n🧪 Testing detect_burst_words...")

        # 配置窗口参数
        BASELINE_LEN = 8
        CURRENT_LEN = 2
        TOTAL_LEN = BASELINE_LEN + CURRENT_LEN

        # 构造虚拟数据流
        # 我们设计一个词 "SuperTopic"，在基线期很低，在当前窗口突然爆发
        # 我们设计一个词 "NormalTopic"，一直很平稳
        
        history_data = []

        # --- Phase 1: Baseline (前8次更新) ---
        for i in range(BASELINE_LEN):
            df = pd.DataFrame({
                'word': ['SuperTopic', 'NormalTopic', 'Noise'],
                'count': [1, 10, 1] # SuperTopic 平均为 1
            })
            history_data.append((datetime.now(), df))

        # --- Phase 2: Current (后2次更新) ---
        for i in range(CURRENT_LEN):
            df = pd.DataFrame({
                'word': ['SuperTopic', 'NormalTopic', 'Noise'],
                'count': [50, 10, 1] # SuperTopic 突然变成 50
            })
            history_data.append((datetime.now(), df))

        # 创建 Mock 队列
        mock_queue = MockHistoryQueue(history_data)

        # 运行函数
        burst_df = detect_burst_words(
            mock_queue, 
            current_window_size=CURRENT_LEN, 
            baseline_window_size=BASELINE_LEN,
            min_freq_now=5,  # 过滤掉 Noise
            min_freq_base=0.5
        )

        print("  [Burst Result Table]:")
        print(burst_df.to_string())

        # 验证逻辑
        # 1. NormalTopic 不应该出现在结果里，或者 fold_change 接近 1
        # 如果它没出现（因为 min_freq_base 或排序），那也没事。但如果出现了，fold_change 应该是 1.0
        if 'NormalTopic' in burst_df['word'].values:
            row = burst_df[burst_df['word'] == 'NormalTopic'].iloc[0]
            self.assertAlmostEqual(row['fold_change'], 1.0, delta=0.2)

        # 2. SuperTopic 应该是突发词
        # 计算预期值：
        # Baseline Total (8 frames) = 1 * 8 = 8. Window Ratio = 8/2 = 4.
        # Baseline Normalized = 8 / 4 = 2.0
        # Current Total (2 frames) = 50 + 50 = 100.
        # Fold Change = 100 / 2.0 = 50.0 (approx)
        
        target_row = burst_df[burst_df['word'] == 'SuperTopic']
        self.assertFalse(target_row.empty, "SuperTopic missed!")
        
        fold_change = target_row.iloc[0]['fold_change']
        freq_base = target_row.iloc[0]['freq_base']
        
        print(f"  [Verification] SuperTopic FoldChange: {fold_change} (Expected ~50.0)")
        
        self.assertAlmostEqual(freq_base, 2.0, delta=0.1)
        self.assertTrue(fold_change > 40, "Fold change should be huge")
        
        print("  ✅ detect_burst_words Passed!")
def generate_simulated_pipeline_data():
    """
    构造符合 detect_burst_words 长度要求的仿真数据
    """
    print("🧪 Starting Pipeline Simulation...")
    
    # 1. 实例化真实的队列
    hq = HistoryDataQueue(max_length=20) # 确保容量够大
    
    # ----------------------------------------
    # 第一阶段：构造 Baseline 数据 (模拟过去的平稳期)
    # ----------------------------------------
    # 我们需要构造足够多的历史数据，让 baseline_window 有东西可算
    # 假设我们想用 baseline_window_size = 5
    
    # 基础词汇：Python一直很火，Crisis以前很少
    base_words = ['Python', 'Data', 'Crisis', 'AI', 'Election']
    base_counts = [100,      80,     5,       60,   20]
    
    # 循环添加 5 次，作为“过去的时间片”
    for i in range(5):
        # 加一点随机波动，显得真实
        counts = [c + np.random.randint(-5, 5) for c in base_counts]
        df_temp = pd.DataFrame({'word': base_words, 'count': counts})
        hq.add(df_temp)
        
    # ----------------------------------------
    # 第二阶段：构造 Current 数据 (模拟最近的爆发期)
    # ----------------------------------------
    # 我们用 current_window_size = 2
    
    # T-1 (倒数第二次): 趋势开始变化
    df_prev = pd.DataFrame({
        'word': ['Python', 'Data', 'Crisis', 'AI', 'Election', 'SuddenMeme'],
        'count': [105,     82,     20,       65,   22,         50] 
    })
    hq.add(df_prev) # Crisis 开始涨了, SuddenMeme 出现了
    
    # T-0 (最新一次): 彻底爆发
    # Crisis: 5 -> 20 -> 100 (Burst!)
    # SuddenMeme: 0 -> 50 -> 300 (New & Burst!)
    df_curr = pd.DataFrame({
        'word': ['Python', 'Data', 'Crisis', 'AI', 'Election', 'SuddenMeme', 'Unknown'],
        'count': [110,     85,     100,      70,   25,         300,          10]
    })
    hq.add(df_curr)
    
    # ----------------------------------------
    # 第三阶段：调用算法 (关键点！)
    # ----------------------------------------
    
    # 目前队列总长度 = 5 (Base) + 2 (Current) = 7
    # 你的函数默认要求 2+8=10，如果不改参数会返回空。
    # 所以我们手动传入 window 参数，适配现有的 7 条数据。
    
    # baseline_window_size 设为 5，current 设为 2，总共需要 7，刚好满足。
    burst_df = detect_burst_words(
        freq_queue=hq,                # 传入队列实例
        current_window_size=2,        # 取最近2个
        baseline_window_size=5,       # 取再之前的5个做基线
        min_freq_now=10,              # 过滤太小的
        top_k=10
    )
    
    # 计算 Trend (常规逻辑)
    recent = hq.get_recent(2)
    df_t1 = recent[0][1]
    df_t0 = recent[1][1]
    trend_result = calculate_word_trends(df_t1, df_t0)
    
    # 补丁：确保 change 字段存在
    for key, df in trend_result.items():
        if not df.empty and 'diff' in df.columns:
            df['change'] = df['diff']

    return trend_result, burst_df
if __name__ == '__main__':
    unittest.main()