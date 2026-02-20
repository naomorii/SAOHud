git clone https://github.com/naomorii/SAOHud.git

cd SAOHud

# Installe les SDK / runtime si nécessaire
flatpak install flathub org.freedesktop.Platform//23.08
flatpak install flathub org.freedesktop.Sdk//23.08
flatpak install flathub org.freedesktop.Sdk.Extension.python3//23.08

# Build et installe localement
flatpak-builder --user --install --force-clean build-dir org.naomorii.SAOHud.yml

# Lance l’application
flatpak run com.naomorii.SAOHud
