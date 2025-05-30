#!/bin/bash
RED='\e[31m'
VERDE='\e[32m'
AZUL='\e[34m'
RESET='\e[0m'

echo -e "${AZUL} \n\n ---SUBDOMAIN TAKOVER--- \n\n ${RESET}"


for palavra in $(cat alvos.txt);do  #Insira sua wordlist

rescname=$(host -t cname $palavra.$1 | grep "alias for")

http=$(curl -s -o /dev/null -w "%{http_code}" "http://$palavra.$1")
conteudo=$(curl -s "http://$palavra.$1")

if [ "$http" -eq 404 ] || [ "$http" -eq 403 ] || [ "$http" -eq 401 ] || [ "$http" -eq 500 ]; then
	echo -e "${RED}[ALERTA] [$palavra.$1] pode estar vulnerável (HTTP $http) ${RESET}";

	if [ -n "$rescname" ]; then
		echo -e "${RED}[ALERTA] CNAME = $rescname ${RESET}"
		 echo "$conteudo" | grep -qiE "No Such Bucket|There's nothing here yet|Domain not found|404 Not Found"
	        echo -e "${RED}[ALERTA] O host demonstrou mensagens vulneráveis a takeover \n ${RESET}"
	else
		echo -e "${RED}[ALERTA] O CNAME não foi encontrado \n ${RESET}"
	fi

else
	echo -e "${VERDE}[$palavra.$1] Subdomínio parece não vulnerável \n ${RESET}"

fi
done
