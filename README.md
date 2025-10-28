# 亚马逊产品评论爬虫

这是一个用于抓取亚马逊产品评论的Python程序，满足以下作业要求：

## 功能特性

1. ✅ **关键词搜索**: 支持通过关键词在亚马逊上搜索产品，并获取搜索结果中前3个产品的详情页链接
2. ✅ **星级筛选**: 支持按照评论星级（5星、4星等）筛选评论
3. ✅ **分页抓取**: 支持分页抓取评论（可配置抓取页数）
4. ✅ **评论信息完整**: 抓取评论内容、评论星级、评论时间、评论者昵称等详细信息
5. ✅ **持久化登录**: 使用Selenium自动化工具登录账户并保存Cookies，实现持久化登录

## 环境要求

- Python 3.7+
- Google Chrome 浏览器
- ChromeDriver（需与Chrome版本匹配）

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装ChromeDriver

#### macOS (使用Homebrew):
```bash
brew install chromedriver
```

#### Windows:
1. 访问 https://chromedriver.chromium.org/downloads
2. 下载与你的Chrome版本匹配的ChromeDriver
3. 将chromedriver.exe放到系统PATH中

#### Linux:
```bash
sudo apt-get install chromium-chromedriver
```

或者手动下载并配置PATH。

## 使用方法

### 基本使用

直接运行程序：

```bash
python amazon_scraper.py
```

首次运行时，程序会：
1. 打开Chrome浏览器
2. 跳转到亚马逊登录页面
3. 等待你手动完成登录（最多120秒）
4. 登录成功后自动保存Cookies到 `amazon_cookies.pkl`
5. 之后的运行会自动使用保存的Cookies

### 自定义配置

在 `amazon_scraper.py` 的 `main()` 函数中修改配置：

```python
def main():
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 配置参数
        search_keyword = "wireless mouse"  # 修改搜索关键词
        star_filters = [5, 4]  # 修改星级筛选: [5, 4, 3, 2, 1] 或 [None]
        pages_per_filter = 2  # 修改每个星级抓取的页数
        
        # 运行爬虫
        scraper.run(
            keyword=search_keyword,
            star_filters=star_filters,
            max_pages=pages_per_filter
        )
```

### 高级用法 - 作为模块使用

```python
from amazon_scraper import AmazonReviewScraper

# 创建爬虫实例
scraper = AmazonReviewScraper(headless=False)

# 加载已保存的Cookies（如果存在）
if not scraper.load_cookies():
    # 首次使用需要登录
    scraper.login_and_save_cookies()

# 搜索产品
products = scraper.search_products("laptop", max_results=3)

# 抓取每个产品的评论
for product in products:
    # 抓取5星评论，2页
    reviews = scraper.scrape_reviews(
        product['url'],
        star_filter=5,
        max_pages=2
    )
    scraper.reviews_data.extend(reviews)

# 保存数据
scraper.save_to_csv("my_reviews.csv")
scraper.save_to_json("my_reviews.json")

# 关闭浏览器
scraper.close()
```

## 输出格式

程序会生成两个文件：

### 1. CSV文件 (`amazon_reviews.csv`)

包含以下字段：
- `product_title`: 产品标题
- `product_url`: 产品链接
- `reviewer_name`: 评论者昵称
- `rating`: 评论星级
- `review_title`: 评论标题
- `review_date`: 评论时间
- `review_content`: 评论内容
- `verified_purchase`: 是否验证购买
- `helpful_count`: 有用投票数
- `scrape_time`: 抓取时间

### 2. JSON文件 (`amazon_reviews.json`)

包含相同的数据，以JSON格式存储，便于程序处理。

## 程序特点

### 1. 持久化登录
- 首次运行时需要手动登录
- Cookies自动保存到 `amazon_cookies.pkl`
- 之后运行自动使用保存的Cookies
- 如果Cookies过期，会提示重新登录

### 2. 反反爬措施
- 使用真实的User-Agent
- 禁用自动化检测标志
- 请求之间添加延迟
- 模拟真实用户行为

### 3. 错误处理
- 完善的异常处理机制
- 超时自动重试
- 优雅地处理缺失数据

### 4. 灵活配置
- 支持无头模式运行（`headless=True`）
- 可自定义抓取页数
- 可选择性筛选星级
- 支持多种保存格式

## 注意事项

1. **合法使用**: 请遵守亚马逊的使用条款和robots.txt，仅用于学习目的
2. **频率控制**: 不要频繁抓取，避免对服务器造成过大压力
3. **账户安全**: 不要分享你的Cookies文件，其中包含登录信息
4. **Chrome版本**: 确保ChromeDriver版本与Chrome浏览器版本匹配
5. **网络环境**: 如果在中国大陆使用，访问amazon.com可能需要网络代理

## 故障排除

### ChromeDriver版本不匹配
```
错误: This version of ChromeDriver only supports Chrome version XX
解决: 更新ChromeDriver或Chrome浏览器使版本匹配
```

### 登录超时
```
错误: 登录超时，请重试
解决: 增加等待时间或手动删除amazon_cookies.pkl重新登录
```

### 找不到元素
```
错误: NoSuchElementException
解决: 亚马逊页面可能已更新，需要更新CSS选择器
```

## 示例输出

```
============================================================
亚马逊产品评论爬虫
============================================================
使用Cookies登录成功！

正在搜索产品: wireless mouse
找到产品 1: Logitech MX Master 3S - Wireless Performance Mouse...
找到产品 2: Razer DeathAdder V2 Pro Wireless Gaming Mouse...
找到产品 3: Microsoft Bluetooth Ergonomic Mouse...
共找到 3 个产品

============================================================
处理产品 1/3
============================================================

正在访问产品页面...
产品: Logitech MX Master 3S

--- 抓取 5 星评论 ---
应用 5 星筛选...
正在抓取第 1 页评论...
本页抓取到 10 条评论
正在抓取第 2 页评论...
本页抓取到 10 条评论

--- 抓取 4 星评论 ---
应用 4 星筛选...
正在抓取第 1 页评论...
本页抓取到 10 条评论
正在抓取第 2 页评论...
本页抓取到 10 条评论

============================================================
抓取完成！共获取 120 条评论
============================================================

数据已保存到 amazon_reviews.csv
共保存 120 条评论

数据已保存到 amazon_reviews.json
共保存 120 条评论

浏览器已关闭
```

## 作业要求完成情况

✅ **要求1**: 支持通过关键词在亚马逊上搜索产品，并获取搜索结果中前3个产品的详情页链接
   - 实现：`search_products()` 方法

✅ **要求2**: 支持按照评论星级筛选，抓取用户评论（至少分页抓取一次）
   - 实现：`scrape_reviews()` 方法，支持 `star_filter` 和 `max_pages` 参数

✅ **要求3**: 使用自动化工具，登录账户获取Cookies，实现爬虫持久化登录
   - 实现：`login_and_save_cookies()` 和 `load_cookies()` 方法

## 许可证

本项目仅用于教育学习目的。

