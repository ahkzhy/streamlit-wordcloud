import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from test_burst_trend import generate_simulated_pipeline_data
from utils import generate_simulated_sentiment_data
from wordcloud import WordCloud
import plotly.express as px
from datetime import datetime, timedelta
import re
from data_processing import analysisData
from updater import start_download_thread
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh # 记得 pip install streamlit-autorefresh


# 每隔 10000 毫秒（10秒）强制 Streamlit 重新运行一遍整个脚本
st_autorefresh(interval=10000, limit=None, key="data_updater")

# 设置matplotlib中文字体（避免警告）
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="Trend Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Real-time Trend Analysis Dashboard")
st.markdown("---")


def generate_wordcloud(df, word_col='word', weight_col='count', title="Word Cloud", max_words=100):
    """生成词云图"""
    if df is None or len(df) == 0:
        return None
    try:
        word_freq = dict(zip(df[word_col], df[weight_col]))
        wordcloud = WordCloud(
            width=900, height=450, background_color='white',
            colormap='viridis', max_words=max_words, relative_scaling=0.5
        ).generate_from_frequencies(word_freq)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(title, fontsize=16, pad=20)
        return fig
    except Exception as e:
        st.error(f"Error generating wordcloud: {e}")
        return None

def generate_combined_wordcloud(df, word_col='word', freq_col='count', tfidf_col='score', title="Combined Word Cloud", max_words=100):
    """生成结合frequency和TF-IDF的词云"""
    if df is None or len(df) == 0:
        return None
    try:
        # 标准化frequency和TF-IDF分数
        freq_values = df[freq_col].values
        tfidf_values = df[tfidf_col].values
        
        # 计算综合分数（frequency * TF-IDF）
        combined_scores = freq_values * tfidf_values
        
        # 创建综合权重字典
        word_weights = dict(zip(df[word_col], combined_scores))
        
        wordcloud = WordCloud(
            width=900, height=450, background_color='white',
            colormap='viridis', max_words=max_words, relative_scaling=0.5
        ).generate_from_frequencies(word_weights)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(title, fontsize=16, pad=20)
        return fig, word_weights
    except Exception as e:
        st.error(f"Error generating combined wordcloud: {e}")
        return None, None



def load_data_files():
    """加载所有数据文件"""
    data_files = {}
    file_mappings = {
    'word_freq': 'word_frequency.csv',
    'word_freq_title': 'word_frequency_title.csv',
    'tfidf': 'tfidf.csv',
    'tfidf_title': 'tfidf_title.csv',
    'articles': 'articles.csv'
}

    
    for key, filename in file_mappings.items():
        try:
            if key == 'articles':
                df = pd.read_csv(filename)
                # 尝试解析时间列
                if 'published_time' in df.columns:
                    df['published_time'] = pd.to_datetime(df['published_time'], errors='coerce')
            else:
                df = pd.read_csv(filename)
            
            # 统一列名
            if key in ['word_freq', 'word_freq_title'] and 'count' in df.columns:
                df = df.rename(columns={'count': 'frequency'})
            
            data_files[key] = df
            print(f"✅ Loaded {filename}")
            
        except FileNotFoundError:
            print(f"❌ {filename} not found, using sample data")
            # 创建示例数据
            if key == 'articles':
                data_files[key] = pd.DataFrame({
                    'id': [1, 2, 3], 'country': ['US', 'UK', 'CA'],
                    'platform': ['news.com', 'blog.org', 'forum.net'],
                    'published_time': pd.to_datetime(['2025-11-13 10:00:00', '2025-11-13 11:00:00', '2025-11-13 12:00:00']),
                    'title': ['Sample 1', 'Sample 2', 'Sample 3'],
                    'content': ['Content 1', 'Content 2', 'Content 3'],
                    'url': ['http://example.com/1', 'http://example.com/2', 'http://example.com/3']
                })
            else:
                data_files[key] = pd.DataFrame({
                    'word': ['technology', 'innovation', 'data', 'analysis', 'research'],
                    'frequency' if key in ['word_freq', 'word_freq_title'] else 'score': [100, 80, 60, 40, 20]
                })
    
    return data_files


def update_data_cache():
    """
    从后端 backend_engine 获取最新数据并适配前端格式
    """
    if 'backend_engine' not in st.session_state:
        st.error("Backend engine not initialized!")
        return

    backend = st.session_state.backend_engine
    with st.spinner("Loading data..."):
        # data_files = load_data_files()
        # if st.session_state.analysis_data is not None:
        #     backend.update_data()
        # ==========================================
        # 2. 提取词频数据 (适配 HistoryDataQueue)
        # ==========================================
        
        # 获取最新的元组 (timestamp, df)
        latest_content_tuple = backend.word_frequency_df.get_latest()
        latest_title_tuple = backend.word_frequency_title_df.get_latest()

        # 解包元组，取出 DataFrame。如果队列为空，给一个空的 DataFrame 防止报错
        if latest_content_tuple:
            _, content_freq_df = latest_content_tuple # 忽略时间戳，只取 df
        else:
            content_freq_df = pd.DataFrame(columns=['word', 'frequency'])

        if latest_title_tuple:
            _, title_freq_df = latest_title_tuple
        else:
            title_freq_df = pd.DataFrame(columns=['word', 'frequency'])

        # ==========================================
        # 3. 提取其他数据 (保持不变)
        # ==========================================
        content_tfidf_df = backend.tfidf_df
        title_tfidf_df = backend.tfidf_title_df
        articles_df = backend.article_df
        sentiment_trend_df = backend.get_sentiment_trend()
        # ==========================================
        # 4. 构建前端数据字典
        # ==========================================   
        analysis_data = {
            'word_data': {
                'content_freq': content_freq_df, 
                'content_tfidf': content_tfidf_df,
                'title_freq': title_freq_df,     
                'title_tfidf': title_tfidf_df
            },
            'platform_data': articles_df,
            'sentiment_data': { 
                'content_desc': backend.get_sentiment_content_top_10_desc(),
                'content_asc': backend.get_sentiment_content_top_10_asc(),
                'title_desc': backend.get_sentiment_title_top_10_desc(),
                'title_asc': backend.get_sentiment_title_top_10_asc(),
                'sentiment_trend': sentiment_trend_df
            },
            'trend_data': {
                'trends': backend.get_word_trends_analysis(),
                'bursts': backend.get_burst_words_analysis(),
                'history_trends': backend.get_history_trends_analysis()
            },
            'last_update': datetime.now(),
            'top_words': {},
            'top_platforms': None
        }
        
        # 预计算top词汇
        for data_type, df in analysis_data['word_data'].items():
            if df is not None and len(df) > 0:
                weight_col = 'count' if 'freq' in data_type else 'score'
                analysis_data['top_words'][data_type] = df.nlargest(20, weight_col)
        
        # 预计算top平台
        if analysis_data['platform_data'] is not None:
            platform_counts = analysis_data['platform_data']['platform'].value_counts().reset_index()
            platform_counts.columns = ['platform', 'count']
            analysis_data['top_platforms'] = platform_counts
        
        st.session_state.analysis_data = analysis_data
        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")

def get_articles_by_platform_and_words(platforms, top_words, articles_df, max_platforms=15):
    """根据平台和关键词获取相关文章"""
    result = {}
    
    # 获取top平台
    top_platform_list = platforms.head(max_platforms)['platform'].tolist()
    
    # 获取top词汇
    keyword_list = top_words['word'].tolist()
    
    for platform in top_platform_list:
        platform_articles = articles_df[articles_df['platform'] == platform]
        
        relevant_articles = []
        for _, article in platform_articles.iterrows():
            title = str(article.get('title', ''))
            url = article.get('url', '')
            
            # 将标题分割成单词列表（只匹配完整单词）
            title_words = re.findall(r'\b\w+\b', title.lower())
            
            # 检查标题是否包含完整的top词汇
            for keyword in keyword_list:
                keyword_lower = keyword.lower()
                if keyword_lower in title_words:
                    relevant_articles.append({
                        'title': title,
                        'url': url,
                        'matched_keyword': keyword
                    })
                    break  # 找到一个匹配就停止，避免重复
        
        if relevant_articles:
            result[platform] = relevant_articles
    
    return result

def main():
    # 初始化session state
    if 'backend_engine' not in st.session_state:
        engine = analysisData()
        start_download_thread(engine) 
        st.session_state.backend_engine = engine
    # 初始化session state
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    if 'cache_expiry' not in st.session_state:
        st.session_state.cache_expiry = datetime.now()
    
    # 加载或更新数据
    if st.session_state.analysis_data is None:
        update_data_cache()
        st.session_state.cache_expiry = datetime.now() + timedelta(seconds=10)
    
    data = st.session_state.analysis_data
    
    # 侧边栏
    with st.sidebar:
        st.header("Control Panel")
        
        data_type = st.radio("Data Type", ["Content Analysis", "Title Analysis"])
        weight_method = st.radio("Weight Method", ["Frequency", "TF-IDF", "Combined"])
        frequency_trend_type=st.radio("Frequency Trend",['common', 'new', 'lost','all'])
        debug_mode = st.checkbox("🛠 Debug Mode (Use Fake Data)", value=False)
        # 缓存状态显示
        if st.session_state.analysis_data:
            last_update = st.session_state.analysis_data['last_update']
            st.write(f"Last update: {last_update.strftime('%H:%M:%S')}")
            
            # 检查是否需要更新缓存（每3小时）
            if datetime.now() > st.session_state.cache_expiry:
                with st.spinner("Cache expired, refreshing data..."):
                    update_data_cache()
                    st.session_state.cache_expiry = datetime.now() + timedelta(seconds=10)
        
        if st.button("🔄 Refresh Data Now"):
            update_data_cache()
            st.session_state.cache_expiry = datetime.now() + timedelta(seconds=10)
            st.rerun()
    

    
    # 确定当前数据源
    if data_type == "Content Analysis":
        current_freq_data = data['word_data']['content_freq']
        current_tfidf_data = data['word_data']['content_tfidf']
        current_data = current_freq_data if weight_method == "Frequency" else current_tfidf_data
        top_words_key = 'content_freq' if weight_method == "Frequency" else 'content_tfidf'
    else:
        current_freq_data = data['word_data']['title_freq']
        current_tfidf_data = data['word_data']['title_tfidf']
        current_data = current_freq_data if weight_method == "Frequency" else current_tfidf_data
        top_words_key = 'title_freq' if weight_method == "Frequency" else 'title_tfidf'
    
    weight_col = 'count' if weight_method == "Frequency" else 'score'
    
    # 主内容区 - 增加第四个标签页用于文章跳转
    tab1, tab2, tab3, tab4,tab5,tab6 = st.tabs([
        "☁️ Word Cloud", 
        "📊 Platform Analysis", 
        "📈 Data Details", 
        "🔗 Article Links",
        "🎭 Sentiment Analysis",
        "🚀 Word Trends"])
    
    with tab1:
        if weight_method == "Combined":
            st.header(f"{data_type} - Combined Frequency & TF-IDF Word Cloud")
            if current_freq_data is not None and current_tfidf_data is not None:
                merged_data = pd.merge(current_freq_data, current_tfidf_data, on='word', suffixes=('_freq', '_tfidf'))
                combined_fig, combined_weights = generate_combined_wordcloud(
                    merged_data, 
                    freq_col='frequency', 
                    tfidf_col='score',
                    title=f"Combined Word Cloud ({data_type})"
                )
                if combined_fig:
                    st.pyplot(combined_fig)
                
                st.subheader("Top 10 Words (Combined Score)")
                if combined_weights:
                    top_words = sorted(combined_weights.items(), key=lambda x: x[1], reverse=True)[:10]
                    top_df = pd.DataFrame(top_words, columns=['word', 'combined_score'])
                    st.dataframe(top_df, use_container_width=True)
                    
                    # 保存top词汇用于文章跳转
                    st.session_state.current_top_words = top_df
            else:
                st.warning("No data available for combined word cloud")
        
        else:
            st.header(f"{data_type} - {weight_method} Word Cloud")
            if current_data is not None and len(current_data) > 0:
                wordcloud_fig = generate_wordcloud(current_data, weight_col=weight_col)
                if wordcloud_fig:
                    st.pyplot(wordcloud_fig)
                
                st.subheader("Top 10 Words")
                top_data = current_data.nlargest(10, weight_col)
                st.dataframe(top_data, use_container_width=True)
                
                # 保存top词汇用于文章跳转
                st.session_state.current_top_words = top_data
            else:
                st.warning("No data available")
    
    with tab2:
        st.header("Platform Distribution")
        if data['platform_data'] is not None and len(data['platform_data']) > 0:
            platform_counts = data['top_platforms']
            
            max_platforms = st.slider("Number of platforms to display", 
                                     min_value=5, 
                                     max_value=min(30, len(platform_counts)), 
                                     value=15)
            
            top_platforms = platform_counts.head(max_platforms)
            
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(
                    top_platforms, 
                    names='platform', 
                    values='count', 
                    title=f"Top {max_platforms} Platforms Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    top_platforms, 
                    x='count', 
                    y='platform', 
                    orientation='h', 
                    title=f"Top {max_platforms} Platforms",
                    color='count',
                    color_continuous_scale='viridis'
                )
                fig_bar.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # 保存top平台用于文章跳转
            st.session_state.current_top_platforms = top_platforms
            
            st.subheader("Platform Statistics")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total Platforms", len(platform_counts))
            with col_stat2:
                coverage = (top_platforms['count'].sum() / platform_counts['count'].sum() * 100) if platform_counts['count'].sum() > 0 else 0
                st.metric(f"Top {max_platforms} Platforms Coverage", f"{coverage:.1f}%")
            with col_stat3:
                st.metric("Most Frequent Platform", 
                         top_platforms.iloc[0]['platform'] if len(top_platforms) > 0 else "N/A")
        else:
            st.info("No article data available")
    
    with tab3:
        st.header("Data Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Last Update", st.session_state.last_refresh)
        with col2:
            if weight_method == "Combined":
                data_to_count = current_freq_data if current_freq_data is not None else current_data
            else:
                data_to_count = current_data
            st.metric("Total Words", len(data_to_count) if data_to_count is not None else 0)
        with col3:
            st.metric("Data Type", data_type)
        with col4:
            st.metric("Weight Method", weight_method)
    
    with tab4:
        st.header("🔗 Relevant Articles by Platform")
        
        # 检查是否有必要的数据
        if ('current_top_words' not in st.session_state or 
            'current_top_platforms' not in st.session_state or 
            data['platform_data'] is None):
            st.info("Please view Word Cloud and Platform Analysis first to load the necessary data.")
        else:
            top_words = st.session_state.current_top_words
            top_platforms = st.session_state.current_top_platforms
            
            st.subheader("Search Criteria")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Top Words:**", ", ".join(top_words['word'].head(10).tolist()))
            with col2:
                st.write("**Top Platforms:**", ", ".join(top_platforms['platform'].head(10).tolist()))
            
            if st.button("🔍 Find Relevant Articles"):
                with st.spinner("Searching for relevant articles..."):
                    relevant_articles = get_articles_by_platform_and_words(
                        top_platforms, 
                        top_words,
                        data['platform_data']
                    )
                    
                    if relevant_articles:
                        st.success(f"Found relevant articles from {len(relevant_articles)} platforms")
                        
                        for platform, articles in relevant_articles.items():
                            with st.expander(f"📰 {platform} ({len(articles)} articles)"):
                                for i, article in enumerate(articles, 1):
                                    st.write(f"{i}. **{article['title']}**")
                                    st.write(f"   🔗 [Open Article]({article['url']})")
                                    st.write(f"   🎯 Matched keyword: `{article['matched_keyword']}`")
                                    st.write("---")
                    else:
                        st.warning("No relevant articles found matching the criteria.")

    with tab5:
        st.header("Sentiment Analysis")
        
        # 从 session_state 获取刚才存进去的情感数据
        sent_data = st.session_state.analysis_data.get('sentiment_data')
        
        if sent_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("😡 Most Negative Content")
                st.dataframe(sent_data['content_asc'], use_container_width=True)
                
                st.subheader("😊 Most Positive Content")
                st.dataframe(sent_data['content_desc'], use_container_width=True)
                
            with col2:
                st.subheader("😡 Most Negative Titles")
                st.dataframe(sent_data['title_asc'], use_container_width=True)
                
                st.subheader("😊 Most Positive Titles")
                st.dataframe(sent_data['title_desc'], use_container_width=True)
        else:
            st.info("Sentiment data is not available.")
        
        st.markdown("---") # 分割线
        # === 新增：情感趋势部分 ===
        st.subheader("❤️ Sentiment Trend Over Time")

        # 获取数据
        sent_trend = data.get('trend_data', {}).get('sentiment_trend', pd.DataFrame())
        if debug_mode:
            st.warning("🧪 Using Simulated Data generated by Real Algorithms")
            # 调用测试用数据
            sent_trend =generate_simulated_sentiment_data()
        # 检查是否有数据 (包括真实数据 或 后面仿真生成的假数据)
        if not sent_trend.empty:
            # Plotly 需要长格式 (Long Format) 来画多条线，或者我们直接手动添加 trace
            # 这里我们简单画个双线图
            
            # 使用 Plotly Express
            # 这里的 x 轴是时间，y 轴是分数
            fig_sent = px.line(
                sent_trend, 
                x='timestamp', 
                y=['avg_content', 'avg_title'], # 同时画两条线
                markers=True,
                title="Average Sentiment Score History",
                labels={'value': 'Sentiment Score', 'timestamp': 'Time', 'variable': 'Source'},
                template="plotly_white"
            )
            
            # 优化一下 Y 轴范围 (通常情感分是 -1 到 1，或者 0 到 1，根据你的数据调整)
            fig_sent.update_yaxes(range=[-1.1, 1.1]) # 假设分数是 -1(负面) 到 1(正面)
            
            # 添加参考线 (0分线)
            fig_sent.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
            
            st.plotly_chart(fig_sent, use_container_width=True)
        else:
            st.info("Accumulating sentiment history... (Wait for next update)")

    with tab6:
        st.header("🚀 Trend & Burst Analysis")
        history_trend_dict = data['trend_data']['history_trends']
        trend_dict = data['trend_data']['trends']
        burst_df = data['trend_data']['bursts']
        if debug_mode:
            st.warning("🧪 Using Simulated Data generated by Real Algorithms")
            # 调用测试用数据
            trend_dict, burst_df = generate_simulated_pipeline_data()
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("📈 Trending Keywords")
    
            # 使用 Tab 分页展示两种不同的视角
            tab_short, tab_long = st.tabs(["⚡ Vs Last Update", "📅 Vs History Avg"])
            with tab_short:
                st.caption("Comparing current frequency with the immediate previous record.")
                if trend_dict:
                    if frequency_trend_type:
                        trend_df=trend_dict[frequency_trend_type]
                        word = trend_df.head(10)
                        
                    else:
                        trend_df=trend_dict["all"]
                        word=trend_df.head(10)
                    # st.dataframe(word, use_container_width=True)
                    if word is not None and not word.empty:
                        cols = st.columns(2) # 2列布局
                        for idx, (index, row) in enumerate(word.iterrows()):
                            c = cols[idx % 2]
                            
                            # 尝试获取 count 和 change，如果没有则给默认值
                            val = row.get('count_new', 0)
                            diff = row.get('freq_change', 0) 
                            
                            c.metric(
                                label=f"{row['word']}", 
                                value=int(val), 
                                delta=f"{int(diff)}" if diff != 0 else None
                            )
                    else:
                        st.info("No trend data available.")
                else:
                    st.info("Not enough history data to calculate trends yet. (Need at least 2 updates)")
            with tab_long:
                st.caption("Comparing current frequency with the average of all history.")
                if history_trend_dict:
                    if frequency_trend_type:
                        trend_df=history_trend_dict[frequency_trend_type]
                        word = trend_df.head(10)
                        
                    else:
                        trend_df=history_trend_dict["all"]
                        word=trend_df.head(10)
                    # st.dataframe(word, use_container_width=True)
                    if word is not None and not word.empty:
                        cols = st.columns(2) # 2列布局
                        for idx, (index, row) in enumerate(word.iterrows()):
                            c = cols[idx % 2]
                            
                            # 尝试获取 count 和 change，如果没有则给默认值
                            val = row.get('count_new', 0)
                            diff = row.get('freq_change', 0) 
                            
                            c.metric(
                                label=f"{row['word']}", 
                                value=int(val), 
                                delta=f"{int(diff)}" if diff != 0 else None
                            )
                    else:
                        st.info("No trend data available.")
                else:
                    st.info("Not enough history data to calculate trends yet. (Need at least 3 updates)")                
        with col_t2:
            st.subheader("💥 Burst Words (Sudden Spikes)")
            if not burst_df.empty:
                if 'burst_score' in burst_df.columns:
                    bursts = burst_df.head(10)
                    st.dataframe(bursts, use_container_width=True)
                    
                    if not bursts.empty:
                        # fig = px.bar(bursts, x='word', y='burst_score', title="Top Burst Scores", color='burst_score')
                        # st.plotly_chart(fig, use_container_width=True)
                        fig = px.scatter(
                            bursts, 
                            x='freq_now', 
                            y='burst_score', 
                            size='fold_change',  # 气泡大小代表翻了多少倍
                            color='burst_score', # 颜色代表爆发得分
                            hover_name='word',   # 鼠标悬停显示单词
                            size_max=40,         # 气泡最大尺寸
                            title="💥 Burst Intensity vs. Volume",
                            labels={'freq_now': 'Current Volume', 'burst_score': 'Burst Intensity'},
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(burst_df)
            else:
                st.info("No burst words detected or insufficient history.")

if __name__ == "__main__":
    main()
