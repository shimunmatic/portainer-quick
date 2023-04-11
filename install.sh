#/bin/bash

API_KEY=$1

mkdir -p ~/.local/share/portainer-quick
cp resources/portainer-quick ~/.local/bin
chmod +x ~/.local/bin/portainer-quick
cp portainer_quick.py ~/.local/share/portainer-quick
cp resources/portainer.svg ~/.local/share/portainer-quick
cp resources/portainer-quick.desktop ~/.local/share/applications/

sed -i "s|HOME_FOLDER|${HOME}|g" ~/.local/share/applications/portainer-quick.desktop

mkdir -p ~/.config/portainer-quick
if [ ! -f ~/.config/portainer-quick/config.json ]
then
  echo -e "{ \"instances\":[{\n\t\"name\": \"Local\",\n\t\"url\": \"http://localhost:9000\",\n\t\"apiKey\":\"${API_KEY}\"\n}]}" > ~/.config/portainer-quick/config.json
fi

pip3 install PyQt6
