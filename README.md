# meshtastic_broadcast
Da circa un mese sto seguendo il progetto Meshtastic che si propone di creare una rete di comunicazione su banda 868Mhz con apparecchi basati su ESP32 e LoRa radio (es.: TTGO-LoRa32-oled). Il progetto include supporto di comunicazione via Python su serial interface collegata a PC. Attraverso la libreria Python meshtastic si può istruire l'unità collegata su porta USB a trasmettere e ricevere messaggi dal mesh configurato. L'applicazione python qui descritta si propone di raccogliere i messaggi di protocollo e di trasmissione dati mostrandoli su PythonQt5 GUI e salvandoli in foglio excell per successive analisi.

## broadcast_msg_pyq5.py
E' l'applicazione pyhon con Qt5 GUI che ha l'obiettivo di mostrare tutti i messaggi che intercorrono nel mesh rilevato dal node connesso sulla porta usb del PC ospite. Il collegamento al node è gestito dalla libreia meshtastic presente in ambiante python avendo in precedenza eseguito 'pip install meshtastic' (senza apici) che fornisce le python API come descritto at https://github.com/meshtastic/Meshtastic-python

