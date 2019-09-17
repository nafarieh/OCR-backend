#import hunspell
from elasticsearch import Elasticsearch

HOST = '192.168.96.88'
#HOST = '127.0.0.1'
PORT = 9200

server_Host = '192.168.96.88'
#server_Host = '127.0.0.1'
server_Port = 7000

#hobj = hunspell.HunSpell('/usr/share/hunspell/fa_IR1.dic','/usr/share/hunspell/fa_IR1.aff')

arabic2persian={'ك':'ک','ي':'ی','ة':'ه'}
symbol=['', '»', ',', ':', '"', '}', '„', '”', '“', '?', '’', ']', '.',  '¿', '‘', '(', ')', ' ', ';', '«', '!', '‚', '{', '¡', '[','؛','ء','،']
