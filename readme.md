# TP Seminario 2022
Este repo presenta una solución desarrollada en el marco del Seminario 2022 de Tópicos
Avanzados en Datos Complejos, de la Especialización en Ciencia de Datos del ITBA.

Creado por C.Olmo colmo@itba.edu.ar, colmo786@gmail.com

## Objetivo de la Solución
Presentar en forma horaria una proyección de la demanda de energía eléctrica de Argentina para las próximas 24 horas.

## Conceptos de la Implementación de la Solución
La solución tiene como tareas macro:
- Obtener en forma horaria el dato de demanda horaria (y temperatura) de energía eléctrica, a nivel total Argentina. Este dato es publicado por una API implementada por la empresa Cammesa. Registrar este dato en una base de datos donde se mantiene la historia.
- Con los datos obtenidos y un modelo pre fiteado, obtener una predicción para las próximas 24 horas.
- Exponer el histórico y la proyección en un dashboard.
La solución se implementó en una serie de containers, permitiendo portabilidad de la solución y reducir tiempo de configuración de los entornos de ejecución de cada bloque de la solución. Se desarrolló en una máquina Windows 10 con 16 Gb de ram. Para poder ejecutar Docker se instaló WSL y luego Docker. Como IDE se utilizó VS Code.
## Esquema de Containers
![image](/docs/images/energy app dockers.png)


