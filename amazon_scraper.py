"""
Amazon Product Review Scraper
抓取亚马逊产品评论信息

功能:
1. 通过关键词搜索产品并获取前3个产品链接
2. 按星级筛选并抓取用户评论（支持分页）
3. 支持登录获取Cookies实现持久化登录
"""

import time
import json
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pickle


class AmazonReviewScraper:
    def __init__(self, headless=False):
        """初始化爬虫"""
        self.driver = self._setup_driver(headless)
        self.cookies_file = "amazon_cookies.pkl"
        self.reviews_data = []
        
    def _setup_driver(self, headless):
        """设置Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # Use a unique user data directory to avoid conflicts
        options.add_argument(f'--user-data-dir=/tmp/amazon_scraper_chrome_{os.getpid()}')
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    
    def login_and_save_cookies(self, email=None, password=None):
        """
        登录亚马逊并保存Cookies
        如果提供了email和password，则自动填写（但仍需手动完成验证）
        否则等待用户手动登录
        """
        print("正在打开亚马逊登录页面...")
        self.driver.get("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
        
        time.sleep(3)
        
        if email and password:
            try:
                # 输入邮箱
                email_input = self.driver.find_element(By.ID, "ap_email")
                email_input.send_keys(email)
                email_input.send_keys(Keys.RETURN)
                time.sleep(2)
                
                # 输入密码
                password_input = self.driver.find_element(By.ID, "ap_password")
                password_input.send_keys(password)
                password_input.send_keys(Keys.RETURN)
                print("已自动填写登录信息，请完成任何额外的验证步骤...")
            except NoSuchElementException:
                print("无法自动填写登录信息，请手动登录...")
        else:
            print("请在浏览器中手动登录亚马逊账户...")
        
        # 等待用户完成登录
        print("等待登录完成（120秒超时）...")
        try:
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.ID, "nav-link-accountList"))
            )
            print("登录成功！")
            
            # 保存Cookies
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
            print(f"Cookies已保存到 {self.cookies_file}")
            return True
            
        except TimeoutException:
            print("登录超时，请重试")
            return False
    
    def load_cookies(self):
        """加载已保存的Cookies"""
        if not os.path.exists(self.cookies_file):
            print(f"未找到Cookies文件: {self.cookies_file}")
            return False
        
        try:
            self.driver.get("https://www.amazon.com")
            time.sleep(2)
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            
            # 刷新页面以应用cookies
            self.driver.refresh()
            time.sleep(2)
            
            # 验证是否登录成功
            try:
                self.driver.find_element(By.ID, "nav-link-accountList")
                print("使用Cookies登录成功！")
                return True
            except NoSuchElementException:
                print("Cookies已过期，需要重新登录")
                return False
                
        except Exception as e:
            print(f"加载Cookies失败: {e}")
            return False
    
    def search_products(self, keyword, max_results=3):
        """
        搜索产品并获取前N个产品的详情页链接
        
        Args:
            keyword: 搜索关键词
            max_results: 获取的产品数量，默认3个
        
        Returns:
            产品链接列表
        """
        print(f"\n正在搜索产品: {keyword}")
        self.driver.get("https://www.amazon.com")
        time.sleep(3)
        
        try:
            # 找到搜索框并输入关键词
            search_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            
            # 等待搜索结果加载
            print("等待搜索结果加载...")
            time.sleep(5)
            
            # 尝试多种选择器来查找产品
            product_links = []
            
            # 尝试方法1: data-component-type
            products = self.driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            print(f"方法1找到 {len(products)} 个产品元素")
            
            # 如果方法1失败，尝试方法2
            if len(products) == 0:
                products = self.driver.find_elements(By.CSS_SELECTOR, "div.s-result-item[data-asin]:not([data-asin=''])")
                print(f"方法2找到 {len(products)} 个产品元素")
            
            for product in products:
                if len(product_links) >= max_results:
                    break
                    
                try:
                    # 尝试多种方式获取产品标题和链接
                    link_element = None
                    
                    # 方法1: h2 a
                    try:
                        link_element = product.find_element(By.CSS_SELECTOR, "h2 a")
                    except:
                        pass
                    
                    # 方法2: a.s-link-style
                    if not link_element:
                        try:
                            link_element = product.find_element(By.CSS_SELECTOR, "a.s-link-style")
                        except:
                            pass
                    
                    # 方法3: 任何包含/dp/的链接
                    if not link_element:
                        try:
                            links = product.find_elements(By.CSS_SELECTOR, "a[href*='/dp/']")
                            if links:
                                link_element = links[0]
                        except:
                            pass
                    
                    if not link_element:
                        continue
                    
                    product_url = link_element.get_attribute("href")
                    product_title = link_element.text.strip()
                    
                    # 如果标题为空，尝试从aria-label获取
                    if not product_title:
                        product_title = link_element.get_attribute("aria-label")
                    
                    # 跳过空标题和URL
                    if not product_title or not product_url:
                        continue
                    
                    # 清理URL（移除多余参数）
                    if "http" in product_url:
                        product_url = product_url.split("?")[0] if "?" in product_url else product_url
                        product_links.append({
                            "title": product_title,
                            "url": product_url
                        })
                        print(f"找到产品 {len(product_links)}: {product_title[:60]}...")
                except Exception as e:
                    # 调试信息
                    # print(f"处理产品时出错: {e}")
                    continue
            
            if len(product_links) == 0:
                # 保存页面截图用于调试
                screenshot_path = "search_page_debug.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"未找到产品，已保存截图到 {screenshot_path}")
            
            print(f"共找到 {len(product_links)} 个产品")
            return product_links
            
        except Exception as e:
            print(f"搜索产品时出错: {e}")
            # 保存错误截图
            try:
                self.driver.save_screenshot("error_screenshot.png")
                print("已保存错误截图到 error_screenshot.png")
            except:
                pass
            return []
    
    def scrape_reviews(self, product_url, star_filter=None, max_pages=2):
        """
        抓取产品评论
        
        Args:
            product_url: 产品详情页URL
            star_filter: 星级筛选 (None, 5, 4, 3, 2, 1)
            max_pages: 抓取的最大页数
        
        Returns:
            评论数据列表
        """
        print(f"\n正在访问产品页面...")
        self.driver.get(product_url)
        time.sleep(3)
        
        try:
            # 获取产品标题
            product_title = self.driver.find_element(By.ID, "productTitle").text
            print(f"产品: {product_title}")
        except:
            product_title = "Unknown Product"
        
        # 点击"查看所有评论"链接
        try:
            # 方法1: 通过链接文本
            see_all_reviews = self.driver.find_element(By.PARTIAL_LINK_TEXT, "customer review")
            see_all_reviews.click()
            time.sleep(3)
        except:
            try:
                # 方法2: 直接构造评论页面URL
                asin = product_url.split("/dp/")[1].split("/")[0] if "/dp/" in product_url else None
                if asin:
                    reviews_url = f"https://www.amazon.com/product-reviews/{asin}"
                    self.driver.get(reviews_url)
                    time.sleep(3)
            except Exception as e:
                print(f"无法访问评论页面: {e}")
                return []
        
        # 应用星级筛选
        if star_filter:
            try:
                print(f"应用 {star_filter} 星筛选...")
                
                # 尝试多种方法来找到星级筛选按钮
                star_element = None
                
                # 方法1: 使用href包含filterByStar
                try:
                    star_filter_xpath = f"//a[contains(@href, 'filterByStar={star_filter}_star')]"
                    star_element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, star_filter_xpath))
                    )
                except:
                    pass
                
                # 方法2: 使用文本匹配
                if not star_element:
                    try:
                        star_text = f"{star_filter} star"
                        star_xpath = f"//a[contains(., '{star_text}')]"
                        star_element = self.driver.find_element(By.XPATH, star_xpath)
                    except:
                        pass
                
                # 方法3: 使用CSS选择器
                if not star_element:
                    try:
                        star_css = f"a[href*='filterByStar={star_filter}_star']"
                        star_element = self.driver.find_element(By.CSS_SELECTOR, star_css)
                    except:
                        pass
                
                if star_element:
                    star_element.click()
                    time.sleep(3)
                    print(f"{star_filter} 星筛选已应用")
                else:
                    print(f"未找到 {star_filter} 星筛选按钮，将抓取所有评论")
                    
            except Exception as e:
                print(f"应用星级筛选失败: {e}，将抓取所有评论")
        
        # 抓取评论
        reviews = []
        for page in range(max_pages):
            print(f"正在抓取第 {page + 1} 页评论...")
            page_reviews = self._extract_reviews_from_page(product_title, product_url)
            reviews.extend(page_reviews)
            print(f"本页抓取到 {len(page_reviews)} 条评论")
            
            # 尝试点击下一页
            if page < max_pages - 1:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                    next_button.click()
                    time.sleep(3)
                except:
                    print("没有更多页面")
                    break
        
        return reviews
    
    def _extract_reviews_from_page(self, product_title, product_url):
        """从当前页面提取评论数据"""
        reviews = []
        
        try:
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-hook='review']")
            
            for review_elem in review_elements:
                try:
                    review_data = {}
                    
                    # 评论者昵称
                    try:
                        reviewer = review_elem.find_element(By.CSS_SELECTOR, ".a-profile-name").text
                        review_data["reviewer_name"] = reviewer
                    except:
                        review_data["reviewer_name"] = "Anonymous"
                    
                    # 评论星级
                    try:
                        rating_element = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='review-star-rating']")
                        rating_text = rating_element.get_attribute("textContent")
                        rating = rating_text.split()[0] if rating_text else "N/A"
                        review_data["rating"] = rating
                    except:
                        review_data["rating"] = "N/A"
                    
                    # 评论标题
                    try:
                        title = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='review-title']").text
                        review_data["review_title"] = title
                    except:
                        review_data["review_title"] = ""
                    
                    # 评论时间
                    try:
                        date = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='review-date']").text
                        review_data["review_date"] = date
                    except:
                        review_data["review_date"] = "N/A"
                    
                    # 评论内容
                    try:
                        content = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='review-body']").text
                        review_data["review_content"] = content
                    except:
                        review_data["review_content"] = ""
                    
                    # 验证购买
                    try:
                        verified = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='avp-badge']")
                        review_data["verified_purchase"] = "Yes"
                    except:
                        review_data["verified_purchase"] = "No"
                    
                    # 有用投票数
                    try:
                        helpful = review_elem.find_element(By.CSS_SELECTOR, "[data-hook='helpful-vote-statement']").text
                        review_data["helpful_count"] = helpful
                    except:
                        review_data["helpful_count"] = "0"
                    
                    # 添加产品信息
                    review_data["product_title"] = product_title
                    review_data["product_url"] = product_url
                    review_data["scrape_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    reviews.append(review_data)
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"提取评论时出错: {e}")
        
        return reviews
    
    def save_to_csv(self, filename="amazon_reviews.csv"):
        """保存评论数据到CSV文件"""
        if not self.reviews_data:
            print("没有数据可保存")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = [
                    'product_title', 'product_url', 'reviewer_name', 'rating',
                    'review_title', 'review_date', 'review_content', 
                    'verified_purchase', 'helpful_count', 'scrape_time'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.reviews_data)
            
            print(f"\n数据已保存到 {filename}")
            print(f"共保存 {len(self.reviews_data)} 条评论")
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
    
    def save_to_json(self, filename="amazon_reviews.json"):
        """保存评论数据到JSON文件"""
        if not self.reviews_data:
            print("没有数据可保存")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.reviews_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n数据已保存到 {filename}")
            print(f"共保存 {len(self.reviews_data)} 条评论")
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
    
    def run(self, keyword, star_filters=[None], max_pages=2):
        """
        运行完整的爬取流程
        
        Args:
            keyword: 搜索关键词
            star_filters: 星级筛选列表，例如 [5, 4] 或 [None] 表示不筛选
            max_pages: 每个产品每个星级抓取的页数
        """
        print("=" * 60)
        print("亚马逊产品评论爬虫")
        print("=" * 60)
        
        # 1. 尝试加载已保存的Cookies
        if not self.load_cookies():
            # 如果加载失败，进行登录
            print("\n请登录亚马逊账户...")
            if not self.login_and_save_cookies():
                print("登录失败，退出程序")
                return
        
        # 2. 搜索产品
        products = self.search_products(keyword, max_results=3)
        
        if not products:
            print("未找到产品，退出程序")
            return
        
        # 3. 对每个产品抓取评论
        for idx, product in enumerate(products, 1):
            print(f"\n{'=' * 60}")
            print(f"处理产品 {idx}/{len(products)}")
            print(f"{'=' * 60}")
            
            for star_filter in star_filters:
                if star_filter:
                    print(f"\n--- 抓取 {star_filter} 星评论 ---")
                else:
                    print(f"\n--- 抓取所有评论 ---")
                
                reviews = self.scrape_reviews(
                    product['url'],
                    star_filter=star_filter,
                    max_pages=max_pages
                )
                self.reviews_data.extend(reviews)
                
                # 添加延迟避免被封
                time.sleep(2)
        
        # 4. 保存数据
        print(f"\n{'=' * 60}")
        print(f"抓取完成！共获取 {len(self.reviews_data)} 条评论")
        print(f"{'=' * 60}")
        
        self.save_to_csv()
        self.save_to_json()
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("\n浏览器已关闭")


def main():
    """主函数 - 使用示例"""
    scraper = AmazonReviewScraper(headless=False)
    
    try:
        # 配置参数
        search_keyword = "wireless mouse"  # 搜索关键词
        star_filters = [5, 4]  # 抓取5星和4星评论，使用 [None] 表示不筛选
        pages_per_filter = 2  # 每个星级抓取2页
        
        # 运行爬虫
        scraper.run(
            keyword=search_keyword,
            star_filters=star_filters,
            max_pages=pages_per_filter
        )
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()

