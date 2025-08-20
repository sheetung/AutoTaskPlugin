import requests

def get_head_image_url():
    # 目标 API 地址
    api_url = "https://zaobao.wpush.cn/api/zaobao/today"
    
    try:
        response = requests.get(api_url)
        # 检查请求是否成功
        if response.status_code == 200:
            # 解析 JSON 数据
            data = response.json()
            # 验证返回状态是否为 success
            if data.get("status") == "success":
                # 提取 image 链接
                image = data["data"].get("image")
                if image and image.startswith("http"):
                    return image
                else:
                    print("未找到有效的 image 链接")
                    return None
            else:
                print(f"API 返回失败：{data.get('message', '未知错误')}")
                return None
        else:
            print(f"获取数据失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        print(f"发生错误：{e}")
        return None

def main():
    image_url = get_head_image_url()  # 获取图片 URL
    if image_url:
        markdown_image_link = f"![Head Image]({image_url})"  # 转换为 Markdown 格式
        print(markdown_image_link)  # 打印 Markdown 图片链接
    else:
        print("无法获取图片或图片链接无效")  # 打印错误信息

if __name__ == "__main__":
    main()