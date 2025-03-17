import requests

def get_zaobao_image_url(token):
    api_url = "https://v3.alapi.cn/api/zaobao"  # API 地址
    params = {
        "token": token,
        "format": "json"  # 指定返回格式为 JSON
    }

    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                # 获取图片 URL
                image_url = data.get("data", {}).get("image")
                if image_url:
                    return image_url
                else:
                    print("未找到图片 URL")
                    return None
            else:
                print(f"API 返回错误：{data.get('msg')}")
                return None
        else:
            print(f"获取图片失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def main():
    token = "0mp7gpcbyvggbh6kexnemzoo1m17yp"  # 替换为你的Token
    image_url = get_zaobao_image_url(token)  # 获取图片 URL
    if image_url and image_url.startswith("http"):
        markdown_image_link = f"![早报图片]({image_url})"  # 转换为 Markdown 格式
        print(markdown_image_link)  # 打印 Markdown 图片链接
    else:
        print("无法获取图片或图片链接无效", end='')  # 打印错误信息

if __name__ == "__main__":
    main()