### XYBotV2 插件


##### api 发送消息  SendMsgApiServer

```

每9秒 读取api传过来消息内容并发送消息


注意首次安装后需要手动 发送 通讯录 触发一次 缓存通讯录列表

后期都会自动更新

每天早上5:30执行 更新通讯录列表


curl --location 'http://127.0.0.1:5688/send_message' \
--header 'Content-Type: application/json' \
--data '{
          "data_list": [
            {
              "receiver_name": ["xxxx"],
              "message": "test 这是一条测试消息",
              "group_name": [
                "xxxxx"

              ]
            }
          ]
        }'

```

##### Apilot 早报插件

```
配置 apikey
```
