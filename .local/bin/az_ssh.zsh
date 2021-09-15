#!/usr/bin/env zsh
emulate -LR zsh
set -o errexit

ID_STR="IdentityFile"
CERT_STR="CertificateFile"
HOST_STR="Hostname"

AZ_HOST=$1
CFG_SSH="${HOME}/.ssh/config"

CFG_AZ="${TMP:-/tmp}/az_ssh.conf"
CFG_TMP="${TMP:-/tmp}/${AZ_HOST}.conf"

CFG_OLD=$(eval awk -v RS='' '/${AZ_HOST}/' ${CFG_SSH})
IP=$(echo ${CFG_OLD} | grep "${HOST_STR}" | awk '{print $2}')

[[ -f ${CFG_AZ} ]] && rm ${CFG_AZ}
az ssh config --ip "${IP}" -f "${CFG_AZ}"
CERT_NEW=$(grep "${CERT_STR}" "${CFG_AZ}" | sed 's/\t//g')
ID_NEW=$(grep "${ID_STR}" "${CFG_AZ}" | sed 's/\t//g')

[[ -f ${CFG_TMP} ]] && rm ${CFG_TMP}
tee ${CFG_TMP} >/dev/null <<EOF
Include ${CFG_SSH}
${CFG_OLD}
EOF

sed -i 's#'"${CERT_STR}"'.*$#'"${CERT_NEW}"'#' ${CFG_TMP}
sed -i 's#'"${ID_STR}"'.*$#'"${ID_NEW}"'#' ${CFG_TMP}

echo "******************"
cat ${CFG_TMP}
echo "******************"
ssh -F ${CFG_TMP} ${AZ_HOST}
