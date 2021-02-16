# meshtastic_broadcast
Da circa un mese sto seguendo il progetto Meshtastic che si propone di creare una rete di comunicazione su banda 868Mhz con apparecchi basati su ESP32 e LoRa radio (es.: TTGO-LoRa32-oled). Il progetto include supporto di comunicazione via Python su serial interface collegata a PC. Attraverso la libreria Python meshtastic si può istruire l'unità collegata su porta USB a trasmettere e ricevere messaggi dal mesh configurato. L'applicazione python qui descritta si propone di raccogliere i messaggi di protocollo e di trasmissione dati mostrandoli su PythonQt5 GUI e salvandoli in foglio excell per successive analisi.

## broadcast_msg_pyq5.py
E' l'applicazione pyhon con Qt5 GUI che ha l'obiettivo di mostrare tutti i messaggi che intercorrono nel mesh rilevato dal node connesso sulla porta usb del PC ospite. Il collegamento al node è gestito dalla libreia meshtastic presente in ambiante python avendo in precedenza eseguito 'pip install meshtastic' (senza apici) che fornisce le python API come descritto at https://github.com/meshtastic/Meshtastic-python

Attraverso interfaccia GUI si può gestire registrazione del colluquio in mesh con o senza invio periodico, ogni 30 secendi, del messaggio presente in input EditText (cui viente automaticamente intestato nomero del messaggio e orario). Questa opzione viene attivata da checkbox esplicativa. Se la checkbox è marcata vengono registrati solo i messaggi automatici generati dal nodo con eventuali risposte, altrimenti oltre a questi vengono inviati i messaggi col testo presente in EditText box.

La seconda checkbox presente serve a eventualmente registrare tutti i messaggi intercorsi nel mesh su file .csv in modo da ottenere poi un excel file da analizzare in seguito. Marcando la checkbox viene aprto in scrittura il file meshtastic_data.csv. La registrazione continua fino a quando non smarchiamo di nuovo la checkbox (il mark viene tolto), momento in cui il .csv file viene chiuso e i relativi dati sono diaponibile per elaborazione excel. Ogni volta che si riapre il file esso viene reinizializzato daccapo.

### Note
Il programma è stato provato con meshtastic Python API 1.1.46 e node firmware 1.1.42. Nel log python ogn tanto appare la scritta WARNING:root:Ignoring old position/user message. Recommend you update firmware to 1.1.20 or later cosa bizzarra perchè il firmware sul node è 1.1.42 e il livello API python è 1.1.46.
In corrispondenza di questo avviso manca poi nel pacchetto ricevuto il campo 'data' e quindi 'portnum' che descive il tipo di messaggi che invece qui è assente. Su questo vedrò di investigare con meshtastic.discounse.group quanto prima.

Il 14 Feb aperto problema at meshtastic.discourse.group e geeksville ha recepito la questione richiedendo una fix per Android App che pare essere lei a inviare i dati GPS in vecchio stile che non viene ticonosciuto da python API che genera poi il warning. Vedi https://github.com/meshtastic/Meshtastic-Android/issues/247
