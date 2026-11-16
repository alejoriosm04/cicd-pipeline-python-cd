# Calculadora Flask: Pipeline CI/CD con AWS ECS y Terraform

Taller Entregable 3: Despliegue Continuo (CD) con AWS ECS e Infraestructura como Código.

## Integrantes

| Nombre completo | Usuario de GitHub | Rol |
|---|---|---|
| Lina Sofia Ballesteros Merchan | [@linaballesteros](https://github.com/linaballesteros) | Colaboradora |
| Alejandro Rios Muñoz | [@alejoriosm04](https://github.com/alejoriosm04) | Propietario del repositorio |
| Quinnie Villarreal | [@quinnie9](https://github.com/quinnie9) | Colaboradora |

## Evidencias

- **Ejecución del pipeline (merge de las nuevas funciones):** https://github.com/alejoriosm04/cicd-pipeline-python-cd/actions/runs/43796974470
- **Pull Request de las nuevas funciones:** https://github.com/alejoriosm04/cicd-pipeline-python-cd/pull/1
- **URLs de los ambientes:**

```plaintext
Staging:    http://calculadora-staging-alb-675256968.us-east-1.elb.amazonaws.com
Production: http://calculadora-production-alb-2091855420.us-east-1.elb.amazonaws.com
```

**Operación nueva en Producción**

<img width="900" height="359" alt="image" src="https://github.com/user-attachments/assets/4afd3ef9-85a9-4acb-bea7-9b2033bf6f80" />
<img width="821" height="232" alt="image" src="https://github.com/user-attachments/assets/94ef2785-9cd2-42f0-95af-6cc3edcae032" />


**Target Group de Producción saludable**

<img width="1666" height="976" alt="image" src="https://github.com/user-attachments/assets/49d45509-055b-4e19-9e88-974a6d4ab855" />


## Respuestas

### 1. Flujo completo del pipeline

**Artefacto que se mueve entre los jobs.** Es la imagen de Docker publicada en Docker Hub con la etiqueta del SHA del commit: `alejoriosm04/cicd-pipeline-python-cd:<sha>`. `build-and-test` la publica y entrega esa URI en el output `image_uri`. `deploy-staging` y `deploy-production` se la pasan a Terraform en la variable `docker_image_uri`, así que ECS descarga en los dos ambientes la misma imagen que ya pasó las pruebas. El SHA también entra al contenedor como `APP_VERSION`, y la aplicación lo muestra en `/health`. La URL del sitio es otra cosa: Terraform la entrega como `alb_url` y se la pasa al job de pruebas de cada ambiente.

**Qué hace cada job.** El recorrido completo empieza cuando el commit se integra en `main`. En un Pull Request solo corre el primer job, y los de despliegue aparecen como omitidos.

1. **`build-and-test`:** verifica el formato con Black, genera los reportes de Pylint y Flake8, ejecuta las pruebas unitarias y de componente con al menos 80 % de cobertura y valida los archivos de Terraform (`fmt -check` y `validate`) sin conectarse al bucket. Luego construye la imagen, la levanta en el runner, ejecuta las pruebas de aceptación contra `localhost` y corre el análisis de SonarCloud. Si la rama es `main`, publica la imagen en Docker Hub con las etiquetas del SHA y `latest`.
2. **`deploy-staging`:** se conecta al estado en S3, selecciona el workspace `staging` y ejecuta `terraform apply` con la URI de la imagen y el SHA. ECS crea una nueva revisión de la task definition y Terraform espera a que el servicio quede estable.
3. **`test-staging`:** consulta `/health` hasta que responda con el SHA del commit y luego repite las pruebas de aceptación con Selenium contra la URL pública de Staging.
4. **Aprobación manual:** es la regla de revisores requeridos del ambiente `production`. `deploy-production` no arranca hasta que un integrante del equipo la aprueba.
5. **`deploy-production`:** repite el `terraform apply` con la misma URI, en el workspace `production`.
6. **`smoke-test-production`:** espera a que el balanceador de Producción responda con el SHA y ejecuta las pruebas de humo.

**Qué valida cada tipo de prueba.**

- **Unitarias:** llaman directamente a las funciones de la calculadora, sin servidor.
- **De componente:** recorren las rutas de Flask, incluida `/health`, con el cliente de prueba.
- **De aceptación:** se ejecutan en local y otra vez en Staging. Abren la página con Selenium y comprueban las operaciones, la división por cero y la entrada de texto inválido.
- **De humo:** solo en Producción. Piden `/` y `/health`: la página debe responder 200 y contener "Calculadora", y el health debe traer `ok` y el SHA de ese commit.

### 2. Terraform frente a la consola, y el estado en S3

**Ventajas.** La principal es que los ambientes quedan iguales. Staging y Producción salen del mismo `main.tf`, y entre uno y otro solo cambian el workspace, el nombre de los recursos y la URI de la imagen. En la consola cada ambiente se arma por separado, clic por clic: toma más tiempo, es más fácil equivocarse y nada garantiza que los dos queden idénticos. Además:

- Cada cambio de infraestructura queda registrado en git, igual que el código.
- El pipeline valida el formato y la sintaxis de los archivos antes de desplegar.
- `terraform apply` muestra qué recursos va a crear, modificar o destruir antes de hacerlo.
- `terraform destroy` borra todo con un comando, lo que ayuda a cuidar el presupuesto del Learner Lab.

**Desventajas.** El tiempo y la dificultad para entender los errores. El primer despliegue del balanceador tarda varios minutos, y cuando Terraform falla, el mensaje es más difícil de seguir que si el mismo recurso se hubiera creado en la consola. También tuvimos que adaptarnos a las restricciones del Learner Lab: Terraform no podía crear el rol IAM ni la red, así que consulta con data sources el `LabRole` y la VPC por defecto que ya existían.

**¿Por qué el estado se guarda en S3 y no en el computador?** Porque desplegamos desde dos lugares: el primer Staging desde un computador local y los siguientes desde el pipeline, en un runner que se borra al terminar. El estado guarda los identificadores de lo que Terraform ya creó (balanceador, cluster, task definitions). Si quedara en el computador, el pipeline no lo vería, intentaría crear todo de nuevo y fallaría con `already exists`. En el bucket `tfstate-calculadora-alejoriosm04`, el computador local y el pipeline leen el mismo archivo.

El bucket además guarda versiones anteriores del estado, `use_lockfile` evita que dos `apply` lo modifiquen a la vez, y cada workspace tiene su propio estado, así que Producción no sobrescribe Staging.

### 3. Ventajas y desventajas de Staging, y velocidad frente a seguridad

**Ventajas.** Cada versión se prueba en AWS antes de llegar a Producción. Staging tiene su propio balanceador, cluster y servicio ECS, creados con el mismo `main.tf` que Producción, así que la imagen corre en las mismas condiciones. Ahí `test-staging` espera a que `/health` muestre el SHA del commit y ejecuta las pruebas de aceptación con Selenium contra la URL pública. Los errores que no aparecen en el contenedor local, como un problema de red, de security group o un health check que falla, se quedan en Staging: el pipeline se detiene y la versión defectuosa nunca llega a Producción. Además, con la aprobación manual, una persona puede probar las operaciones nuevas en Staging antes de liberar.

**Desventajas.** El costo y el tiempo. Cada ambiente cuesta cerca de USD 0,05 por hora (unos USD 1,2 por día), y Staging sigue cobrando aunque nadie lo use. Cada despliegue también tarda más, porque suma un `terraform apply`, la espera a que la versión nueva quede saludable, las pruebas con Selenium y la aprobación de un integrante.

**Velocidad frente a seguridad.** El despliegue se vuelve más lento pero más seguro. Incluso una versión correcta tiene que esperar ese paso extra. Preferimos perder unos minutos y detectar el error en Staging que enterarnos cuando ya afecta a los usuarios en Producción.

### 4. Diferencia entre `test-staging` y `smoke-test-production`

**En Staging** corren las pruebas de aceptación completas. Primero el job espera a que `/health` devuelva el SHA del commit, para no probar la versión anterior. Después Selenium abre la calculadora, llena el formulario y comprueba cada operación, la división por cero y los números inválidos.

**En Producción** corren las pruebas de humo. Con `urllib`, sin navegador, se piden `/` y `/health`: la página debe responder 200 y mostrar "Calculadora", y el health debe traer `ok` y el SHA de esa ejecución. No se vuelven a probar las operaciones.

**¿Por qué esta diferencia?** El comportamiento de la aplicación ya se validó en Staging, donde todavía se puede frenar la promoción si algo falla. En Producción, que es el sitio público, solo confirmamos rápido y con poco tráfico de prueba que quedó sirviendo la versión correcta.

### 5. Dos partes que aún le faltan al pipeline

**1. Alertas después del despliegue.** Hoy CloudWatch guarda los logs durante siete días, y el pipeline vigila el servicio solo mientras dura el release. Si más tarde un target queda `unhealthy` o aumentan los errores 5xx, nadie se entera. Esto importa porque los problemas también aparecen después de desplegar. Se puede resolver con una alarma de CloudWatch por ambiente, definida en Terraform, sobre la métrica de hosts unhealthy del target group o sobre los errores 5xx del balanceador, que envíe una notificación al equipo por SNS.

**2. Credenciales sin llaves copiadas (OIDC).** Hoy copiamos a GitHub la access key, el secret y el session token cada vez que vence la sesión de cuatro horas del laboratorio, y un token vencido hace fallar el despliegue. Además, guardar llaves en secretos es un riesgo de seguridad. En una cuenta real se usa OIDC: AWS confía en GitHub Actions mediante un rol IAM, y cada ejecución recibe credenciales temporales que vencen solas. No lo implementamos porque el Learner Lab no permite crear roles ni proveedores de identidad.

### 6. Experiencia al implementar las dos funciones nuevas

**Lina Sofia Ballesteros Merchan:** Revisé el Pull Request de potencia y módulo, lo aprobé y lo integré a `main`. En la ejecución del merge, Staging quedó en verde y, antes de soltar Producción, las operaciones nuevas ya respondían ahí. Aprobé el environment `production` con el comentario de que en Staging se comportaban bien. El pipeline me sirvió porque el despliegue no dependía de repetir los pasos en la consola y la espera de aprobación dejaba un registro de quién liberó esa versión. Lo que menos ayudó fue el tiempo entre el merge y poder aprobar: hay que esperar el `apply` de Staging y las pruebas con Selenium.

**Alejandro Rios Muñoz:** Como propietario, el pipeline del repositorio usa las cuentas de Docker Hub, SonarCloud y AWS del laboratorio. En el Pull Request, `build-and-test` mostró el formato, la cobertura y las pruebas de aceptación locales antes de integrar, y los jobs de despliegue aparecieron como omitidos hasta el merge. Después del merge, Staging se actualizó solo y en `/health` se podía confirmar el SHA `04a7ca33cf0e87a70213aaad0aec58c1e4731c7a`. El CI/CD sirvió para no repetir el despliegue a mano. Lo que menos ayudó fue la espera del `apply` hasta que ECS estabiliza el servicio, y que Pylint y Flake8 dejen observaciones sin frenar el job.

**Quinnie Villarreal:** Implementé potencia y módulo en la calculadora, actualicé el formulario y agregué pruebas unitarias, de componente y de aceptación, incluyendo errores como módulo por cero. Las 38 pruebas unitarias y de componente pasaron con cobertura del 100 %, y el CI del PR fue aprobado. Aprendí cómo las ramas, los Pull Requests y las pruebas automáticas permiten revisar los cambios antes de integrarlos. Lo más útil fue recibir resultados automáticos sobre mi implementación; la configuración de permisos y ambientes requirió mayor coordinación con el equipo.

### 7. Entrega continua, revisión en Staging y fallo del health check

**¿Entrega Continua o Despliegue Continuo?** Con la aprobación manual, el pipeline implementa **Entrega Continua**. Staging se actualiza solo en cada merge a `main`, pero Producción espera a que un revisor la libere. Antes de configurar esa regla era Despliegue Continuo, porque `deploy-production` arrancaba apenas `test-staging` quedaba en verde.

**¿Qué revisamos antes de aprobar?** Abrimos la URL de Staging y probamos potencia y módulo en la calculadora. También comprobamos que `/health` mostrara el SHA del merge y que `test-staging` hubiera terminado en verde. La aprobación de Producción en esa ejecución quedó con el comentario: "Las funcionalidades agregadas se comportan correctamente en staging, por lo tanto se aprueba para el despliegue."

**¿Qué haría ECS si la versión nueva no pasa el health check?**

- **El balanceador** consulta `/health` cada 30 segundos. Después de tres fallos seguidos marca la tarea como `unhealthy` y deja de enviarle tráfico.
- **ECS** detiene esa tarea y lanza otra. Mientras tanto, la tarea anterior sigue atendiendo, porque ECS solo la retira cuando la nueva está saludable, así que el servicio no se cae.
- **El circuit breaker**, si la versión nueva sigue fallando, marca el despliegue como fallido y vuelve automáticamente a la última task definition que funcionaba.

**¿Cómo lo detecta el pipeline?** `terraform apply` termina con error porque el servicio no llega a un estado estable. Si eso no pasa, `/health` sigue mostrando el SHA anterior y falla el paso de espera de `test-staging` o de `smoke-test-production`. Si ocurre en Staging, el pipeline se detiene y esa versión nunca llega a Producción.
