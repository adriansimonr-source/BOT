import dxcam


camera = dxcam.create()


print(
    "Camera creada"
)


print(
    "Monitores disponibles:"
)


print(
    dxcam.output_info()
)