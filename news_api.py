# News scraping from CNA (Channel News Asia) only
import requests
from bs4 import BeautifulSoup

def get_content_from_url(url):
    """
    Scrape the content of news from specified URL

    Args:
        url (str): URL to the news

    Returns:
        content (str): The contents scrapped
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")

        content_elements = soup.select("div.text > div.text-long") # CNA organizes their content in this format

        content_list = []
        for content_element in content_elements:
            # Extract text from all <p> elements within the content_element
            content = "\n".join(p.text.strip() for p in content_element.find_all("p"))
            content_list.append(content)

        if len(content_list) > 1:
            return "\n".join(content_list)  # Join with line breaks if thr are multiple elements 
        elif len(content_list) == 1:
            return content_list[0]  # Return the single content element
        else:
            return ""  # Return empty string if no content elements found
        
    except requests.exceptions.RequestException as e:
        # Handle HTTP request errors
        print(f"Error fetching content: {e}")
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An error occurred: {e}")
        return None

def get_news(topic='drug',start_date=None ,end_date=None):
    """
    Fetches news articles from News API.

    Args:
        topic (str): Domain to search for. Only 'drug' or 'vape' are supported.
        requested_end_date (str): Date for when the API is called in 'yyyy-mm-dd' format.

    Returns:
        list: A list of dictionaries, each representing a news article with metadata & content.
    """
    access_key = '2f171ec4cf714f03844528984d7d7e4f'
    base_url = 'https://newsapi.org/v2/everything'
    
    # Request parameters
    params = {
        'apiKey': access_key,
        'q': topic,
        'domains': 'channelnewsasia.com',
        'language': 'en',
        'pageSize': 10,
        'sortBy': 'relevancy',
        'from': start_date,
        'to': end_date
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'ok' and 'articles' in data:
            articles = []
            for article in data['articles']:
                article['content'] = get_content_from_url(article['url'])
                articles.append({k: article[k] for k in ['title', 'url', 'publishedAt', 'content']})
            return articles
        else:
            print("No articles found in the response.")
    else:
        print("Error:", response.status_code)
        print(response.json())
    
    return []  # Return an empty list if no articles are found


