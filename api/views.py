from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
import requests
import xml.etree.ElementTree as ET
from django.views.decorators.csrf import csrf_exempt
import json
import xml.sax.saxutils as saxutils
from rest_framework.response import Response
from django.core.paginator import Paginator
from math import ceil
import datetime 
from .models import Commande
from .serializers import CommandeSerializer

@api_view(['GET'])
def get_clients(request):
    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:wss="http://www.adonix.com/WSS"
                      xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
        <soapenv:Header/>
        <soapenv:Body>
            <wss:query>
                <wss:callContext>
                    <codeLang>FRA</codeLang>
                    <poolAlias>SEED</poolAlias>
                    <requestConfig>adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
                </wss:callContext>
                <publicName>BPC</publicName>
                <objectKeys soapenc:arrayType="wss:CAdxParamKeyValue[]"/>
                <listSize>999999</listSize>
            </wss:query>
        </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "query"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False  # ⚠️ pour dev uniquement
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        # XML parsing
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS'
        }

        root = ET.fromstring(response.content)
        body = root.find('soapenv:Body', namespaces)
        query_response = body.find('wss:queryResponse', namespaces)
        query_return = query_response.find('queryReturn', namespaces)
        result_elem = query_return.find('resultXml', namespaces)

        if result_elem is None or not result_elem.text:
            return JsonResponse({"error": "Pas de données retournées"}, status=500)

        cdata = result_elem.text.strip()
        result_root = ET.fromstring(cdata)

        all_clients = []
        for lin in result_root.findall('LIN'):
            client = {}
            for fld in lin.findall('FLD'):
                name = fld.attrib.get('NAME')
                value = fld.text.strip() if fld.text else ''
                if name == 'BPCNUM':
                    client['code'] = value
                elif name == 'BPCNAM':
                    client['nom'] = value
                elif name == 'CUR':
                    client['devise'] = value
            all_clients.append(client)

        # ✅ Pagination manuelle
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        total = len(all_clients)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_clients = all_clients[start:end]

        return JsonResponse({
            "results": paginated_clients,
            "count": total,
            "page": page,
            "page_size": page_size,
        })

    except Exception as e:
        return JsonResponse({
            "error": "Erreur serveur Django",
            "details": str(e)
        }, status=500)

@api_view(['GET'])
def get_articles(request):
    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:wss="http://www.adonix.com/WSS"
                      xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
        <soapenv:Header/>
        <soapenv:Body>
            <wss:query>
                <wss:callContext>
                    <codeLang>FRA</codeLang>
                    <poolAlias>SEED</poolAlias>
                    <requestConfig>adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
                </wss:callContext>
                <publicName>WSITM</publicName>
                <objectKeys soapenc:arrayType="wss:CAdxParamKeyValue[]"/>
                <listSize>999999</listSize>
            </wss:query>
        </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "query"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        root = ET.fromstring(response.content)
        body = root.find('soapenv:Body', namespaces)
        query_response = body.find('wss:queryResponse', namespaces)
        query_return = query_response.find('queryReturn', namespaces)
        result_elem = query_return.find('resultXml', namespaces)

        cdata = result_elem.text.strip()
        result_root = ET.fromstring(cdata)

        all_articles = []
        for lin in result_root.findall('LIN'):
            article = {}
            for fld in lin.findall('FLD'):
                name = fld.attrib.get('NAME')
                value = fld.text.strip() if fld.text else ''
                if name == 'ITMREF':
                    article['code_article'] = value
                elif name == 'C2':
                    article['designation'] = value
            all_articles.append(article)

        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        paginator = Paginator(all_articles, page_size)
        paginated_articles = paginator.get_page(page)

        return Response({
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "current_page": page,
            "results": list(paginated_articles)
        })

    except Exception as e:
        return JsonResponse({
            "error": "Erreur serveur Django",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
def get_sites(request):
    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:wss="http://www.adonix.com/WSS"
                      xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
        <soapenv:Header/>
        <soapenv:Body>
            <wss:query>
                <wss:callContext>
                    <codeLang>FRA</codeLang>
                    <poolAlias>SEED</poolAlias>
                    <requestConfig>adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
                </wss:callContext>
                <publicName>SITES</publicName>
                <objectKeys soapenc:arrayType="wss:CAdxParamKeyValue[]"/>
                <listSize>999999</listSize>
            </wss:query>
        </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "query"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        root = ET.fromstring(response.content)
        body = root.find('soapenv:Body', namespaces)
        query_response = body.find('wss:queryResponse', namespaces)
        query_return = query_response.find('queryReturn', namespaces)
        result_elem = query_return.find('resultXml', namespaces)

        cdata = result_elem.text.strip()
        result_root = ET.fromstring(cdata)

        all_sites = []
        for lin in result_root.findall('LIN'):
            site = {}
            for fld in lin.findall('FLD'):
                name = fld.attrib.get('NAME')
                value = fld.text.strip() if fld.text else ''
                if name == 'FCY':
                    site['code_site'] = value
                elif name == 'FCYNAME':
                    site['designation'] = value
            all_sites.append(site)

        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        paginator = Paginator(all_sites, page_size)
        paginated_articles = paginator.get_page(page)

        return Response({
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "current_page": page,
            "results": list(paginated_articles)
        })

    except Exception as e:
        return JsonResponse({
            "error": "Erreur serveur Django",
            "details": str(e)
        }, status=500)



import datetime

def format_date_sage(date_str):
    """Convertit 'dd/MM/yyyy' en 'YYYYMMDD'."""
    if not date_str:
        return ''
    try:
        dt = datetime.datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y%m%d")
    except ValueError:
        return ''

import xml.etree.ElementTree as ET

import xml.etree.ElementTree as ET

def get_sohnum_from_sage_response(response_content):
    # Décoder bytes → str
    xml_string = response_content.decode('utf-8')

    # Parser la réponse SOAP avec namespaces
    namespaces = {
        'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
        'wss': 'http://www.adonix.com/WSS'
    }
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        print("Erreur parsing SOAP:", e)
        return None, None

    body = root.find('soapenv:Body', namespaces)
    if body is None:
        return None, None

    save_response = body.find('wss:saveResponse', namespaces)
    if save_response is None:
        return None, None

    save_return = save_response.find('saveReturn', namespaces)
    if save_return is None:
        return None, None

    result_elem = save_return.find('resultXml', namespaces)
    if result_elem is None or result_elem.text is None:
        return None, None

    cdata_content = result_elem.text.strip()

    # Remplacer les caractères spéciaux & non-échappés
    import re
    cdata_content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', cdata_content)

    # Parser le XML à l'intérieur du CDATA
    try:
        result_root = ET.fromstring(cdata_content)
    except ET.ParseError as e:
        print("Erreur parsing CDATA:", e)
        return None, cdata_content

    # Récupérer SOHNUM (GRP commençant par SOH0)
    sohnum = None
    for grp in result_root.findall('GRP'):
        grp_id = grp.attrib.get('ID', '')
        if grp_id.startswith('SOH0'):
            fld = grp.find('FLD[@NAME="SOHNUM"]')
            if fld is not None and fld.text:
                sohnum = fld.text.strip()
                break

    return sohnum, cdata_content


@api_view(['POST'])
def valider_commande(request):
    data = request.data
    entete = data.get('entete', {})
    livraison = data.get('livraison', {})
    lignes = data.get('lignes', [])

    # --- Construction XML ---
    root = ET.Element('PARAM')

    # GRP SOH0_1
    grp_soh0_1 = ET.SubElement(root, 'GRP', ID='SOH0_1')
    ET.SubElement(grp_soh0_1, 'FLD', NAME='SALFCY', TYPE='Char').text = entete.get('site_vente', '')
    ET.SubElement(grp_soh0_1, 'FLD', NAME='SOHTYP', TYPE='Char').text = entete.get('type_commande', '')
    ET.SubElement(grp_soh0_1, 'FLD', NAME='ORDDAT', TYPE='Date').text = format_date_sage(entete.get('date_commande', ''))
    ET.SubElement(grp_soh0_1, 'FLD', NAME='BPCORD', TYPE='Char').text = entete.get('code_client', '')

    # GRP SOH2_1
    grp_soh2_1 = ET.SubElement(root, 'GRP', ID='SOH2_1')
    ET.SubElement(grp_soh2_1, 'FLD', NAME='STOFCY', TYPE='Char').text = livraison.get('site_expedition', '')

    # GRP SOH2_2
    grp_soh2_2 = ET.SubElement(root, 'GRP', ID='SOH2_2')
    ET.SubElement(grp_soh2_2, 'FLD', NAME='DEMDLVDAT', TYPE='Date').text = format_date_sage(livraison.get('date_livraison') or '')
    ET.SubElement(grp_soh2_2, 'FLD', NAME='SHIDAT', TYPE='Date').text = format_date_sage(livraison.get('date_expedition') or '')

    # TAB SOH4_1
    tab_soh4_1 = ET.SubElement(root, 'TAB', ID='SOH4_1', SIZE=str(len(lignes)), DIM='300')
    for idx, ligne in enumerate(lignes, start=1):
        lin = ET.SubElement(tab_soh4_1, 'LIN', NUM=str(idx))
        ET.SubElement(lin, 'FLD', NAME='NUMLIG', TYPE='Integer').text = str(idx)
        ET.SubElement(lin, 'FLD', NAME='ITMREF', TYPE='Char').text = ligne.get('code_article', '')
        ET.SubElement(lin, 'FLD', NAME='QTY', TYPE='Decimal').text = str(ligne.get('quantite_commandee', 0))

    xml_payload = ET.tostring(root, encoding='utf-8').decode('utf-8')

    # --- Enveloppe SOAP ---
    soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wss="http://www.adonix.com/WSS">
      <soapenv:Header/>
      <soapenv:Body>
        <wss:save>
          <callContext>
            <codeLang>FRA</codeLang>
            <poolAlias>SEED</poolAlias>
            <poolId></poolId>
            <requestConfig></requestConfig>
          </callContext>
          <publicName>WSCOMCLT</publicName>
          <objectXml><![CDATA[{xml_payload}]]></objectXml>
        </wss:save>
      </soapenv:Body>
    </soapenv:Envelope>
    """

    # --- Envoi vers Sage ---
    try:
        response = requests.post(
            "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC",
            data=soap_envelope,
            headers={'Content-Type': 'text/xml; charset=utf-8', 
                     "SOAPAction": "save"},
            auth=('username', 'pwd')
        )

    except requests.RequestException as e:
        return Response({"error": f"Erreur de connexion à Sage : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- Parsing réponse ---
    try:
        sohnum, cdata = get_sohnum_from_sage_response(response.content)
        commande_id = int(data.get("id"))
        if commande_id:  
            Commande.objects.filter(id=commande_id).update(
            statut="validee",
            id_sage=sohnum
        )
        return Response({
            "message": "Commande envoyée à Sage et validée",
            "id_sage": sohnum,
            "xml_envoye": xml_payload,
            "xml_recu": cdata
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_client_details(request, code_client):
    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    xml_request = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                                        xmlns:wss="http://www.adonix.com/WSS"
                                        xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
       <soapenv:Header/>
       <soapenv:Body>
          <wss:read>
             <callContext>
                <codeLang>FRA</codeLang>
                <poolAlias>SEED</poolAlias>
                <poolId/>
                <requestConfig>adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
             </callContext>
             <publicName>BPC</publicName>
             <objectKeys soapenc:arrayType="wss:CAdxParamKeyValue[]">
                <item>
                   <key>BPCNUM</key>
                   <value>{code_client}</value>
                </item>
             </objectKeys>
          </wss:read>
       </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "read"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False  # ⚠️ uniquement pour dev
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        root = ET.fromstring(response.content)
        body = root.find('.//soapenv:Body', namespaces)
        if body is None:
            return JsonResponse({"error": "Pas de corps SOAP dans la réponse", "raw": response.text}, status=500)

        result_elem = body.find('.//resultXml', namespaces)
        if result_elem is None or not result_elem.text:
            return JsonResponse({
                "error": f"Aucune donnée renvoyée pour le client '{code_client}'",
                "raw": response.text
            }, status=404)

        cdata = result_elem.text.strip()
        result_root = ET.fromstring(cdata)

        # Parcourir tous les GRP pour récupérer les champs du client
        fields = {}
        for grp in result_root.findall('.//GRP'):
            for fld in grp.findall('FLD'):
                name = fld.attrib.get('NAME')
                value = fld.text.strip() if fld.text else ''
                if name not in fields:
                    fields[name] = value

        client_data = {
            "code_client": fields.get("BPCNUM"),
            "raison_sociale": fields.get("BPCNAM"),
            "devise": fields.get("CUR")
        }

        return JsonResponse(client_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import requests
import xml.etree.ElementTree as ET

@api_view(['POST'])
def get_article_stock(request):
    print("Données reçues :", request.data)
    site = request.data.get("site")
    date = format_date_sage(request.data.get("date"))
    article = request.data.get("article")

    if not site or not date or not article:
        return JsonResponse({"error": "Champs manquants (site, date, article)"}, status=400)

    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    # Construction de la requête SOAP avec inputXml encodé
    xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:wss="http://www.adonix.com/WSS"
                  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
   <soapenv:Header/>
   <soapenv:Body>
      <wss:run soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
         <callContext xsi:type="wss:CAdxCallContext">
            <codeLang xsi:type="xsd:string">FRA</codeLang>
            <poolAlias xsi:type="xsd:string">SEED</poolAlias>
            <requestConfig xsi:type="xsd:string">adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
         </callContext>
         <publicName xsi:type="xsd:string">STCKDISPON</publicName>
         <inputXml>&lt;PARAM&gt;&lt;GRP ID="GRP1"&gt;&lt;FLD NAME="LFCY" TYPE="Char"&gt;{site}&lt;/FLD&gt;&lt;FLD NAME="LITM" TYPE="Char"&gt;{article}&lt;/FLD&gt;&lt;FLD NAME="LDAT" TYPE="Date"&gt;{date}&lt;/FLD&gt;&lt;/GRP&gt;&lt;/PARAM&gt;</inputXml>
      </wss:run>
   </soapenv:Body>
</soapenv:Envelope>
"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "run"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        # Parse réponse SOAP
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS',
        }

        root = ET.fromstring(response.content)
        result_elem = root.find('.//resultXml', namespaces)

        if result_elem is None or not result_elem.text:
            return JsonResponse({"error": "Aucune donnée de Sage X3", "raw": response.text}, status=404)

        # Contenu XML renvoyé par Sage (dans CDATA)
        cdata = result_elem.text.strip()
        result_root = ET.fromstring(cdata)

        # Cherche la quantité disponible dans LQTY
        quantity = None
        for fld in result_root.findall('.//FLD'):
            if fld.attrib.get('NAME') == "LQTY":
                quantity = fld.text
                break

        if quantity is None:
            return JsonResponse({
                "error": "Impossible de trouver LQTY dans la réponse",
                "raw": cdata
            }, status=404)

        return JsonResponse({
            "article": article,
            "site": site,
            "date": date,
            "quantite": quantity
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
def get_article_details(request, code_article):
    url_sage = "http://192.168.1.110:8124/soap-generic/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC"
    sage_user = "username"
    sage_password = "pwd"

    xml_request = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                                        xmlns:wss="http://www.adonix.com/WSS"
                                        xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
       <soapenv:Header/>
       <soapenv:Body>
          <wss:read>
             <callContext>
                <codeLang>FRA</codeLang>
                <poolAlias>SEED</poolAlias>
                <poolId/>
                <requestConfig>adxwss.optreturn=XML;adxwss.beautify=true</requestConfig>
             </callContext>
             <publicName>WSITM</publicName>
             <objectKeys soapenc:arrayType="wss:CAdxParamKeyValue[]">
                <item>
                   <key>ITMREF</key>
                   <value>{code_article}</value>
                </item>
             </objectKeys>
          </wss:read>
       </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "read"
    }

    try:
        response = requests.post(
            url_sage,
            data=xml_request,
            headers=headers,
            auth=(sage_user, sage_password),
            timeout=30,
            verify=False  # ⚠️ uniquement pour dev
        )

        if response.status_code != 200:
            return JsonResponse({
                "error": f"Erreur HTTP {response.status_code} depuis Sage X3",
                "details": response.text
            }, status=500)

        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wss': 'http://www.adonix.com/WSS',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        # Parse la réponse SOAP
        root = ET.fromstring(response.content)
        body = root.find('.//soapenv:Body', namespaces)
        if body is None:
            return JsonResponse({"error": "Pas de corps SOAP dans la réponse", "raw": response.text}, status=500)

        # Cherche resultXml peu importe le namespace
        result_elem = body.find('.//resultXml', namespaces)
        if result_elem is None or not result_elem.text:
            return JsonResponse({
                "error": f"Aucune donnée renvoyée pour l'article '{code_article}'",
                "raw": response.text
            }, status=404)

        cdata = result_elem.text.strip()

        # Parse le contenu XML renvoyé par Sage
        result_root = ET.fromstring(cdata)

        # Parcourir tous les GRP pour récupérer les champs
        fields = {}
        for grp in result_root.findall('.//GRP'):
             for fld in grp.findall('FLD'):
                name = fld.attrib.get('NAME')
                value = fld.text.strip() if fld.text else ''
                # Ne pas écraser si le champ existe déjà
                if name not in fields:
                 fields[name] = value

        article_data = {
    "code": fields.get("ITMREF"),
    "designation": fields.get("DES1AXX"),
    "unite_stock": fields.get("STU"),
    "coef_stock_vente": fields.get("SAUSTUCOE"),
    "prix": fields.get("BASPRI")
}
        return JsonResponse(article_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from rest_framework import status
@api_view(['POST'])
def save_commande(request):
    try:
        # On récupère les champs envoyés
        entete = request.data.get('entete')
        livraison = request.data.get('livraison')
        lignes = request.data.get('lignes')
        client_sage = request.data.get('client_sage')
        articles_sage = request.data.get('articles_sage')

        # On stocke le formulaire complet dans un seul champ JSON
        data_formulaire = {
            "entete": entete,
            "livraison": livraison,
            "lignes": lignes
        }

        commande = Commande.objects.create(
            user=request.user,
            data_formulaire=data_formulaire,
            client_sage=client_sage,
            articles_sage=articles_sage,
            statut="non_validee"
        )

        return Response(
            {
                "message": "Commande enregistrée avec succès",
                "id": commande.id
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def commandes_validees(request):
    # On filtre par l'utilisateur connecté + statut validée
    commandes = Commande.objects.filter(user=request.user, statut='validee').order_by('-date_created')

    # On prépare la réponse JSON
    data = []
    for cmd in commandes:
        data.append({
            "id": cmd.id,
            "date_created": cmd.date_created.strftime("%Y-%m-%d %H:%M"),
            "statut": cmd.statut,
            "client_sage": cmd.client_sage,
            "articles_sage": cmd.articles_sage,
            "id_sage":cmd.id_sage,
        })

    return Response(data, status=status.HTTP_200_OK)


def nettoyer_codes_articles(data_formulaire: dict) -> dict:

    lignes = data_formulaire.get("lignes", [])
    for ligne in lignes:
        code_article = ligne.get("code_article", "")
        # Nettoyage de base
        code_article = code_article.strip().upper()
        # Optionnel : remplacer caractères interdits par Sage
        # code_article = re.sub(r"[^A-Z0-9]", "", code_article)
        ligne["code_article"] = code_article
    data_formulaire["lignes"] = lignes
    return data_formulaire


@api_view(['GET'])
def commandes_non_validees(request):
    commandes = Commande.objects.filter(
        user=request.user,
        statut='non_validee'
    ).order_by('-date_created')

    data = []
    for cmd in commandes:
        data.append({
            "id": cmd.id,
            "date_created": cmd.date_created.strftime("%Y-%m-%d %H:%M"),
            "statut": cmd.statut,
            "client_sage": cmd.client_sage or {},
            "articles_sage": cmd.articles_sage or [],
            "data_formulaire": cmd.data_formulaire,  # <-- Ajouté
        })

    return Response(data, status=status.HTTP_200_OK)
