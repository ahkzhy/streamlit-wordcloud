import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
from datetime import datetime, timedelta
import re

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

# 初始化session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None

def get_english_stopwords():
    """获取英文停用词列表"""
    english_stopwords = {
        # 基础冠词、连词、介词
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while', 
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
        'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
        'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', "don't", "should", 
        "now", "'s", "'t", "'m", "'re", "'ve", "'d", "'ll", "n't", 'be', 'is', 'are', 
        'was', 'were', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
        'did', 'doing', 
        
        # 新增连词
        'also', 'although', 'though', 'since', 'unless', 'whether', 'while', 'whereas',
        'therefore', 'thus', 'hence', 'consequently', 'moreover', 'furthermore', 
        'however', 'nevertheless', 'nonetheless', 'otherwise', 'instead', 'meanwhile',
        
        # 时间相关词汇
        'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'hour', 
        'hours', 'minute', 'minutes', 'second', 'seconds', 'time', 'times', 'season',
        'seasons', 'today', 'tomorrow',
        'yesterday', 'now', 'then', 'when', 'before', 'after', 'during', 'while',
        'moment', 'period', 'date', 'calendar', 'clock', 'schedule',
        
        # 数字和序数词
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth',
        'ninth', 'tenth', 'once', 'twice', 'thrice', 'single', 'double', 'triple',
        'number', 'numbers', 'count', 'total', 'amount', 'quantity',
        
        # 常见代词和人称
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours',
        'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves',
        'yourselves', 'themselves',
        
        # 常见助动词和情态动词
        'may', 'might', 'must', 'shall', 'should', 'would', 'could', 'ought','said'
        
        # 标点符号和特殊字符
        '', ' ', '  ', ',', '.', '!', '?', ':', ';', '-', '(', ')', 
        '[', ']', '{', '}', '/', '\\', '|', '@', '#', '$', '%', '^', '&', '*', '+', '=', 
        '<', '>', '~', '_', '"', "'", '`',
        
        # 常见无意义词汇
        'very', 'really', 'quite', 'rather', 'pretty', 'just', 'even', 'still', 'yet',
        'already', 'almost', 'nearly', 'hardly', 'scarcely', 'simply', 'merely',
        'actually', 'basically', 'essentially', 'literally', 'virtually'
    }
    
    # 添加单个字母
    english_stopwords.update([chr(i) for i in range(97, 123)])
    english_stopwords.update([chr(i) for i in range(65, 91)])
    
    # 添加数字
    english_stopwords.update([str(i) for i in range(0, 100)])
    
    return english_stopwords

def is_english_word(word):
    """检查单词是否只包含英文字母"""
    if not isinstance(word, str):
        return False
    # 使用正则表达式检查是否只包含英文字母（允许连字符和撇号）
    return bool(re.match(r'^[a-zA-Z\-\.\']+$', word))

def clean_with_stopwords(df, word_col='word'):
    """使用停用词列表清理数据"""
    stop_words = get_english_stopwords()
    
    def is_valid_word(word):
        if pd.isna(word) or not isinstance(word, str):
            return False
        
        word_clean = word.strip().lower()
        
        # 检查是否是停用词
        if word_clean in stop_words:
            return False
        
        # 检查是否只包含英文字母
        if not is_english_word(word):
            return False
        
        # 检查单词长度
        if len(word_clean) <= 1:
            return False
        
        # 检查是否全是特殊字符
        if re.match(r'^[^\w\s]+$', word_clean):
            return False
            
        return True
    
    original_count = len(df)
    cleaned_df = df[df[word_col].apply(is_valid_word)].copy()
    return cleaned_df, original_count - len(cleaned_df)

def generate_wordcloud(df, word_col='word', weight_col='frequency', title="Word Cloud", max_words=100):
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

def generate_combined_wordcloud(df, word_col='word', freq_col='frequency', tfidf_col='score', title="Combined Word Cloud", max_words=100):
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

import time
from datetime import datetime, timedelta

def update_data_cache():
    """更新数据缓存"""
    with st.spinner("Loading data..."):
        data_files = load_data_files()
        
        # 清理词汇数据
        for key in ['word_freq', 'word_freq_title', 'tfidf', 'tfidf_title']:
            if key in data_files:
                data_files[key], removed_count = clean_with_stopwords(data_files[key])
                print(f"Cleaned {key}: removed {removed_count} stopwords")
        
        # 创建分析数据词典
        analysis_data = {
            'word_data': {
                'content_freq': data_files.get('word_freq'),
                'content_tfidf': data_files.get('tfidf'),
                'title_freq': data_files.get('word_freq_title'),
                'title_tfidf': data_files.get('tfidf_title')
            },
            'platform_data': data_files.get('articles'),
            'last_update': datetime.now(),
            'top_words': {},
            'top_platforms': None
        }
        
        # 预计算top词汇
        for data_type, df in analysis_data['word_data'].items():
            if df is not None and len(df) > 0:
                weight_col = 'frequency' if 'freq' in data_type else 'score'
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
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    if 'cache_expiry' not in st.session_state:
        st.session_state.cache_expiry = datetime.now()
    
    # 侧边栏
    with st.sidebar:
        st.header("Control Panel")
        
        data_type = st.radio("Data Type", ["Content Analysis", "Title Analysis"])
        weight_method = st.radio("Weight Method", ["Frequency", "TF-IDF", "Combined"])
        
        # 缓存状态显示
        if st.session_state.analysis_data:
            last_update = st.session_state.analysis_data['last_update']
            st.write(f"Last update: {last_update.strftime('%H:%M:%S')}")
            
            # 检查是否需要更新缓存（每3小时）
            if datetime.now() > st.session_state.cache_expiry:
                st.warning("Cache expired, refreshing data...")
                update_data_cache()
                st.session_state.cache_expiry = datetime.now() + timedelta(hours=3)
        
        if st.button("🔄 Refresh Data Now"):
            update_data_cache()
            st.session_state.cache_expiry = datetime.now() + timedelta(hours=3)
            st.rerun()
    
    # 加载或更新数据
    if st.session_state.analysis_data is None:
        update_data_cache()
        st.session_state.cache_expiry = datetime.now() + timedelta(hours=3)
    
    data = st.session_state.analysis_data
    
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
    
    weight_col = 'frequency' if weight_method == "Frequency" else 'score'
    
    # 主内容区 - 增加第四个标签页用于文章跳转
    tab1, tab2, tab3, tab4 = st.tabs(["☁️ Word Cloud", "📊 Platform Analysis", "📈 Data Details", "🔗 Article Links"])
    
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

if __name__ == "__main__":
    main()
