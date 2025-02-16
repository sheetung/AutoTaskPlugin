import requests

def get_anime_image_url():
    api_url = "https://api.03c3.cn/api/zb"  # API 地址

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            # 如果返回状态码是 200，直接将 API 地址作为图片 URL
            return api_url
        else:
            print(f"获取图片失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def main():
    image_url = get_anime_image_url()  # 获取图片 URL
    if image_url and image_url.startswith("http"):
        markdown_image_link = f"![Anime Image]({image_url})"  # 转换为 Markdown 格式
        print(markdown_image_link)  # 打印 Markdown 图片链接
    else:
        print("无法获取图片或图片链接无效")  # 打印错误信息

if __name__ == "__main__":
    main()