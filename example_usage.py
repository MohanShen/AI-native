"""
亚马逊评论爬虫 - 使用示例
简化版使用示例，展示如何使用爬虫
"""

from amazon_scraper import AmazonReviewScraper


def example_1_basic_usage():
    """示例1: 基本使用 - 搜索产品并抓取所有评论"""
    print("\n" + "="*60)
    print("示例1: 基本使用")
    print("="*60)
    
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 运行爬虫 - 抓取所有评论（不按星级筛选）
        scraper.run(
            keyword="laptop",
            star_filters=[None],  # 不筛选星级
            max_pages=1  # 每个产品抓取1页
        )
    finally:
        scraper.close()


def example_2_star_filtering():
    """示例2: 星级筛选 - 只抓取5星和4星评论"""
    print("\n" + "="*60)
    print("示例2: 星级筛选")
    print("="*60)
    
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 只抓取5星和4星评论
        scraper.run(
            keyword="headphones",
            star_filters=[5, 4],
            max_pages=2  # 每个星级抓取2页
        )
    finally:
        scraper.close()


def example_3_manual_control():
    """示例3: 手动控制 - 分步执行各个操作"""
    print("\n" + "="*60)
    print("示例3: 手动控制流程")
    print("="*60)
    
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 步骤1: 登录（首次使用）或加载Cookies
        if not scraper.load_cookies():
            print("需要登录...")
            scraper.login_and_save_cookies()
        
        # 步骤2: 搜索产品
        products = scraper.search_products("wireless keyboard", max_results=2)
        
        # 步骤3: 对第一个产品抓取评论
        if products:
            print(f"\n只处理第一个产品: {products[0]['title']}")
            
            # 抓取5星评论
            reviews_5star = scraper.scrape_reviews(
                products[0]['url'],
                star_filter=5,
                max_pages=1
            )
            scraper.reviews_data.extend(reviews_5star)
            print(f"5星评论数量: {len(reviews_5star)}")
            
            # 抓取1星评论
            reviews_1star = scraper.scrape_reviews(
                products[0]['url'],
                star_filter=1,
                max_pages=1
            )
            scraper.reviews_data.extend(reviews_1star)
            print(f"1星评论数量: {len(reviews_1star)}")
        
        # 步骤4: 保存数据
        scraper.save_to_csv("manual_reviews.csv")
        scraper.save_to_json("manual_reviews.json")
        
    finally:
        scraper.close()


def example_4_all_star_ratings():
    """示例4: 抓取所有星级 - 分别抓取5/4/3/2/1星"""
    print("\n" + "="*60)
    print("示例4: 抓取所有星级评论")
    print("="*60)
    
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 抓取所有星级的评论
        scraper.run(
            keyword="usb cable",
            star_filters=[5, 4, 3, 2, 1],  # 所有星级
            max_pages=1  # 每个星级1页
        )
    finally:
        scraper.close()


if __name__ == "__main__":
    print("亚马逊评论爬虫 - 使用示例")
    print("\n请选择运行哪个示例:")
    print("1. 基本使用 - 搜索并抓取所有评论")
    print("2. 星级筛选 - 只抓取5星和4星")
    print("3. 手动控制 - 分步执行操作")
    print("4. 所有星级 - 分别抓取5/4/3/2/1星")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        example_1_basic_usage()
    elif choice == "2":
        example_2_star_filtering()
    elif choice == "3":
        example_3_manual_control()
    elif choice == "4":
        example_4_all_star_ratings()
    else:
        print("无效选项，运行默认示例...")
        example_2_star_filtering()

