# 快速开始指南

## 📦 安装

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装ChromeDriver
```bash
# macOS
brew install chromedriver

# 或者从官网下载：https://chromedriver.chromium.org/downloads
```

## 🚀 运行程序

### 方法1: 直接运行（推荐）
```bash
python amazon_scraper.py
```

首次运行会打开浏览器登录页面，登录后程序自动保存Cookies。之后运行会自动使用保存的Cookies。

### 方法2: 运行示例程序
```bash
python example_usage.py
```
会提供4个不同的使用示例供选择。

## ⚙️ 自定义配置

编辑 `amazon_scraper.py` 的 `main()` 函数:

```python
def main():
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # ===== 在这里修改配置 =====
        search_keyword = "wireless mouse"  # 修改搜索关键词
        star_filters = [5, 4]              # 修改星级: [5,4,3,2,1] 或 [None]
        pages_per_filter = 2               # 修改每个星级抓取的页数
        # ========================
        
        scraper.run(
            keyword=search_keyword,
            star_filters=star_filters,
            max_pages=pages_per_filter
        )
```

### 配置示例

#### 只抓取5星评论，每个产品3页
```python
search_keyword = "laptop"
star_filters = [5]
pages_per_filter = 3
```

#### 抓取所有星级，每个产品1页
```python
search_keyword = "headphones"
star_filters = [5, 4, 3, 2, 1]
pages_per_filter = 1
```

#### 不筛选星级，抓取所有评论
```python
search_keyword = "keyboard"
star_filters = [None]
pages_per_filter = 2
```

## 📊 输出文件

运行后会生成以下文件:

1. **amazon_reviews.csv** - CSV格式的评论数据（可用Excel打开）
2. **amazon_reviews.json** - JSON格式的评论数据（便于程序处理）
3. **amazon_cookies.pkl** - 保存的登录Cookies（自动生成）

## 📋 输出数据字段

每条评论包含以下信息:
- `product_title` - 产品标题
- `product_url` - 产品链接
- `reviewer_name` - 评论者昵称 ⭐
- `rating` - 评论星级 ⭐
- `review_title` - 评论标题
- `review_date` - 评论时间 ⭐
- `review_content` - 评论内容 ⭐
- `verified_purchase` - 是否验证购买
- `helpful_count` - 有用投票数
- `scrape_time` - 抓取时间

## 🔧 常见问题

### Q: 提示"ModuleNotFoundError: No module named 'selenium'"
**A**: 运行 `pip install -r requirements.txt` 安装依赖

### Q: 提示"chromedriver not found"
**A**: 安装ChromeDriver: `brew install chromedriver`

### Q: Cookies过期了怎么办？
**A**: 删除 `amazon_cookies.pkl` 文件，重新运行程序会提示登录

### Q: 找不到产品怎么办？
**A**: 
1. 检查网络连接
2. 确认关键词拼写正确
3. 查看生成的截图文件 `search_page_debug.png`

### Q: 星级筛选不工作？
**A**: 程序会自动回退到抓取所有评论，不影响数据收集

### Q: 想要抓取更多产品？
**A**: 修改 `search_products()` 的 `max_results` 参数

## 💡 高级用法

### 作为Python模块使用
```python
from amazon_scraper import AmazonReviewScraper

scraper = AmazonReviewScraper(headless=False)

# 登录
if not scraper.load_cookies():
    scraper.login_and_save_cookies()

# 搜索产品
products = scraper.search_products("laptop", max_results=5)

# 抓取评论
for product in products:
    reviews = scraper.scrape_reviews(
        product['url'],
        star_filter=5,
        max_pages=3
    )
    scraper.reviews_data.extend(reviews)

# 保存数据
scraper.save_to_csv("my_data.csv")
scraper.close()
```

### 无头模式运行（不显示浏览器）
```python
scraper = AmazonReviewScraper(headless=True)
```

## 📝 注意事项

1. **首次使用**: 需要手动登录一次，之后会自动使用保存的Cookies
2. **频率控制**: 不要过于频繁运行，避免被Amazon检测
3. **合法使用**: 仅用于学习目的，遵守Amazon使用条款
4. **网络要求**: 需要能访问 amazon.com（在中国可能需要代理）

## 🎯 作业要求对照

✅ **要求1**: 关键词搜索并获取前3个产品链接 - `search_products()`  
✅ **要求2**: 星级筛选和分页抓取评论 - `scrape_reviews()`  
✅ **要求3**: Selenium自动化登录并保存Cookies - `login_and_save_cookies()`

所有功能已测试通过！详见 `HOMEWORK_VERIFICATION.md`

## 📞 问题反馈

如遇到问题，请查看:
1. `README.md` - 完整文档
2. `HOMEWORK_VERIFICATION.md` - 作业验证文档
3. 生成的截图文件 - 用于调试

