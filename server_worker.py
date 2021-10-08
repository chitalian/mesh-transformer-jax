from server_queue import QueueWorker
import json
# def infer(x):
#     pass
class ServerWorker(QueueWorker):
    def __init__(self):
        from server_mesh_analyzer import infer
        self.infer = infer

    def run(self, input: str) -> str:
        print("RUNNING WORKER")
        kwargs = {}
        try:
            content = json.loads(input)
            body = content.get('body', 'no body found!')
            params = content.get('params', {}) 
            if top_k := params.get('top_k', None):
                kwargs['top_k'] = top_k
            if top_p := params.get('top_p', None):
                kwargs['top_p'] = top_p
            if temp := params.get('temp', None):
                kwargs['temp'] = temp
            if gen_len := params.get('gen_len', None):
                kwargs['gen_len'] = gen_len                

        except json.decoder.JSONDecodeError as e:
            print(type(e))
            body = input
        
        # print(content)
        # sleep(1)
        # print(str(input.decode('utf-8')))
        # '_thread._local' object has no attribute 'env'
        # threading.local().env
        print(f'Running infer with args:\n{kwargs}\n\nbody:{body[:10]}...')
        x = self.infer(body, **kwargs)
        print("DONE WORKING")
        print(x)
        return x[0]
