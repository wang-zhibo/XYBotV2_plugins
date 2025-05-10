### XYBotV2 插件


##### api 发送消息  SendMsgApiServer

```



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
