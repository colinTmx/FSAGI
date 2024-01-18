from langchain_core.tools import BaseTool
from typing import Optional
from langchain.callbacks.manager import CallbackManagerForToolRun
import oss2
from config.config import *
from urllib.parse import urljoin
import json
import time
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import os


class AsrTool(BaseTool):
    name: str = "asr_tool"
    description: str = """当需要识别音频文件，该文件格式属于[".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma"]时，可以通过本工具从音频文件中提取文本，该工具输入文件名称，输出音频对应的文本内容"""

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        path = os.path.join(os.getcwd(), "uploaded_files")
        file = os.path.join(path, query)
        auth = oss2.Auth(accessKeyId, accessKeySecret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        bucket.put_object_from_file(query, file)
        fileLink = urljoin(file_link_prefix, query)
        REGION_ID = "cn-shanghai"
        PRODUCT = "nls-filetrans"
        DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
        API_VERSION = "2018-08-17"
        POST_REQUEST_ACTION = "SubmitTask"
        GET_REQUEST_ACTION = "GetTaskResult"
        KEY_APP_KEY = "appkey"
        KEY_FILE_LINK = "file_link"
        KEY_VERSION = "version"
        KEY_ENABLE_WORDS = "enable_words"
        KEY_AUTO_SPLIT = "auto_split"
        KEY_TASK = "Task"
        KEY_TASK_ID = "TaskId"
        KEY_STATUS_TEXT = "StatusText"
        KEY_RESULT = "Result"
        STATUS_SUCCESS = "SUCCESS"
        STATUS_RUNNING = "RUNNING"
        STATUS_QUEUEING = "QUEUEING"
        auto_split = "auto_split"
        speaker_num = "speaker_num"
        rate_adaptive = "enable_sample_rate_adaptive"
        client = AcsClient(accessKeyId, accessKeySecret, REGION_ID)
        postRequest = CommonRequest()
        postRequest.set_domain(DOMAIN)
        postRequest.set_version(API_VERSION)
        postRequest.set_product(PRODUCT)
        postRequest.set_action_name(POST_REQUEST_ACTION)
        postRequest.set_method("POST")
        task = {
            KEY_APP_KEY: appKey,
            KEY_FILE_LINK: fileLink,
            KEY_VERSION: "4.0",
            KEY_ENABLE_WORDS: False,
            auto_split: True,
            rate_adaptive: True,
            speaker_num: 2,
        }
        task = json.dumps(task)
        postRequest.add_body_params(KEY_TASK, task)
        taskId = ""
        try:
            postResponse = client.do_action_with_exception(postRequest)
            postResponse = json.loads(postResponse)
            print(postResponse)
            statusText = postResponse[KEY_STATUS_TEXT]
            if statusText == STATUS_SUCCESS:
                print("录音文件识别请求成功响应！")
                taskId = postResponse[KEY_TASK_ID]
            else:
                print("录音文件识别请求失败！")
                return
        except ServerException as e:
            print(e)
        except ClientException as e:
            print(e)
        getRequest = CommonRequest()
        getRequest.set_domain(DOMAIN)
        getRequest.set_version(API_VERSION)
        getRequest.set_product(PRODUCT)
        getRequest.set_action_name(GET_REQUEST_ACTION)
        getRequest.set_method("GET")
        getRequest.add_query_param(KEY_TASK_ID, taskId)
        while True:
            try:
                getResponse = client.do_action_with_exception(getRequest)
                getResponse = json.loads(getResponse)
                statusText = getResponse[KEY_STATUS_TEXT]
                if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING:
                    time.sleep(10)
                else:
                    break
            except ServerException as e:
                print(e)
            except ClientException as e:
                print(e)
        if statusText == STATUS_SUCCESS:
            print("录音文件识别成功！")
        else:
            print("录音文件识别失败！")
        data = getResponse["Result"]["Sentences"]
        result = "对话内容："
        result += " ".join([d["SpeakerId"] + "：" + d["Text"] for d in data])
        # for d in data:
        #     result +=",".join(d["SpeakerId"]+ "：" +d["Text"])
        return result
