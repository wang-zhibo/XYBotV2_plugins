### XYBotV2 插件


##### api 发送消息  SendMsgApiServer

```

每六秒 读取api传过来消息内容并发送消息

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
