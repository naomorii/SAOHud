git clone https://github.com/naomorii/SAOHud.git

cd SAOHud

# Installe les SDK / runtime si nécessaire
flatpak install flathub org.gnome.Platform//45

flatpak install flathub org.gnome.Sdk//45


# Build et installe localement
flatpak-builder --user --install --force-clean build-dir org.naomorii.SAOHud.yml

# Lance l’application
flatpak run com.naomorii.SAOHud
