import socket
import pickle
import random
import time

HEADERSIZE = 10

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = socket.gethostname()
port = 1234

s.bind((ip, port))
s.listen(5)

while 1:
           
    try:
        clientsocket, address = s.accept()
                
        datos = {
                    1: random.randint(25,30)  ,
                    2: random.randint(40,90),
                    3: random.randint(40,90),
                    4: random.randint(90,100),
                    5: random.randint(2,40),
                    6: str(random.randint(100,150))+'/'+str(random.randint(70,120)),
                    7: range(0,1502),
                    8: range(0,102),
                    9: range(0,102),               
                    }
        msg = pickle.dumps(datos)
                    
        msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8')+msg
        #print('o',self.define)
        clientsocket.send(msg)
        clientsocket.close()
    
        time.sleep(0.050)
    except Exception as e:
        print(e)
