import requests
import json

# response = requests.get('http://115.156.214.117:40002/')
# response = requests.get('http://115.156.214.117:40002/reset')
# response2 = requests.get('http://115.156.214.117:40002/a')
# with open('1.jpg','rb') as f:
#     response3 = requests.post('http://115.156.214.117:40002/u', files={'file': f})
# print(response.text)
# print(response2.text)
# a=json.loads(response2.text)
# print(a)
# print(response3.content)
# response4 = requests.get('http://115.156.214.117:40002/get_file/top10.png')
# with open('2.png','wb') as f:
#     for chunk in response4.iter_content(100000):
#         f.write(chunk)
# print(response4.content)
response = requests.get('http://115.156.214.117:40002/box/1')
print(response.text)
with open('./res/box.jpg', 'wb') as f:
    for chunk in response.iter_content(100000):
        f.write(chunk)