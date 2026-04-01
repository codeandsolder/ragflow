#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import ragflow_sdk

API_KEY = "ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
BASE_URL = "http://127.0.0.1:9380"


def main():
    ragflow = ragflow_sdk.RAGFlow(api_key=API_KEY, base_url=BASE_URL)

    datasets = ragflow.list_datasets(id="your_dataset_id")
    for dataset in datasets:
        print(f"Dataset: {dataset.name} (ID: {dataset.id})")
        chats = ragflow.list_chats(dataset_id=dataset.id)
        for chat in chats:
            print(f"  Chat: {chat.name} (ID: {chat.id})")
            sessions = chat.list_sessions()
            for session in sessions:
                print(f"    Session: {session.id}")

    ragflow.close()


if __name__ == "__main__":
    main()
