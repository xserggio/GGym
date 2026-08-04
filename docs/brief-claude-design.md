# Brief para Claude Design — App de entrenamiento de fuerza

> Pegar este documento entero como primer mensaje en Claude Design.

---

## Qué estamos diseñando

Una aplicación web instalable en el móvil para llevar el registro de entrenamientos de fuerza en el gimnasio. La usan dos personas, cada una con su perfil. No es una app social, no es una app de nutrición y no tiene comunidad: es un instrumento personal de registro y progresión.

**El contexto de uso manda sobre todo lo demás.** Se usa de pie, entre serie y serie, con una mano, con las manos sudadas, con prisa y con auriculares puestos. Cada interacción tiene que resolverse con el pulgar en menos de tres segundos. Si un elemento es bonito pero requiere precisión al tocarlo, está mal diseñado.

**El usuario tipo no conoce los ejercicios por su nombre.** Necesita reconocer visualmente la máquina antes de leer nada. Las imágenes no son decoración: son el sistema de navegación primario.

---

## Dirección visual

No busques el look de app de fitness: nada de fondos negros con degradados neón, siluetas musculadas ni tipografía condensada agresiva. Tampoco el look de app de productividad genérica.

La referencia es **el material impreso del propio gimnasio**: las fichas de entrenamiento en papel, las placas laterales de las máquinas con el diagrama del movimiento, el código de colores internacional de los discos olímpicos. Un instrumento de taller, no un producto de estilo de vida.

### Paleta

Derivada del código de color de los discos de competición, que es un sistema que ya existe en el mundo del usuario y que se lee de un vistazo.

| Rol | Hex | Uso |
|---|---|---|
| Cemento | `#E9E7E2` | Fondo de aplicación |
| Papel | `#F7F6F3` | Tarjetas y superficies elevadas |
| Tinta | `#14161A` | Texto principal, controles primarios |
| Grafito | `#6B7076` | Texto secundario, bordes hairline |
| Disco azul | `#2B5FD9` | Acción principal, estado activo |
| Disco verde | `#2E8B57` | Serie completada |
| Disco amarillo | `#F2C230` | Cronómetro en marcha |
| Disco rojo | `#D2333C` | Récord personal, avisos |

El azul es el único color de la interfaz general. Los otros tres viven exclusivamente en estados y en la visualización de peso. Fondo claro por defecto: el gimnasio está iluminado con fluorescentes y una pantalla oscura se llena de reflejos. Incluye variante oscura como secundaria, con `#16181A` de fondo y la misma familia de acentos.

### Tipografía

- **Display**: una grotesca **ancha o expandida** (Archivo Expanded, Degular Display o similar). Contradeliberada frente a la condensada típica del fitness. Se usa con moderación: nombre de la sesión y cifras grandes.
- **Cuerpo**: Inter, pesos 400 y 500.
- **Datos**: una monoespaciada con cifras tabulares (IBM Plex Mono o JetBrains Mono) para pesos, repeticiones, cronómetros y todo lo que sea número. Los números tienen que alinearse en columna y no bailar al cambiar de valor.

Escala amplia: el peso de la serie actual es el elemento más grande de la pantalla, del orden de 48-56 px. Todo lo demás muy por debajo.

### Elemento firma

**La barra cargada.** Cada peso se representa además de con la cifra, con una miniatura esquemática de una barra con sus discos, coloreados según el código real. 82,5 kg se dibuja como barra + azul + azul + amarillo + rojo pequeño. Se aprende a leer en dos sesiones y aparece en el historial, en los récords y en la fila de serie.

Es lo único con licencia para ser llamativo. Todo lo demás queda callado: tarjetas con borde hairline de 1 px en grafito al 20%, sin sombras pesadas, radio de esquina 10 px constante.

---

## Pantallas a diseñar

Formato móvil, 390 × 844. Diseña también los estados vacíos y de carga de cada una.

### 1. Hoy
Pantalla de entrada. Domina una tarjeta grande con la sesión que toca ahora ("Sesión 2 · Pierna (fuerza)"), la lista resumida de sus ejercicios con miniaturas, y un botón **Empezar** de ancho completo anclado abajo.

Debajo, dos módulos menores: cronómetro de cinta de andar (start/stop) y peso corporal de la semana.

Un indicador discreto de la rueda: cinco marcas 1-5 con la posición actual resaltada. No es un calendario. La app no muestra días de la semana como estructura.

### 2. Sesión activa
La pantalla crítica. Lista de ejercicios de la sesión, cada uno como tarjeta plegable con su miniatura a la izquierda.

Al desplegar, sus series como filas. **La fila de serie es el componente más importante de la app**: número de serie, peso, repeticiones y un check grande. Peso y reps se ajustan con botones `−` / `+` de al menos 44 px (incrementos de 2,5 kg y 1 rep), con opción de teclear. Al marcar la serie, la fila pasa a verde disco y arranca el cronómetro de descanso.

Cronómetro de descanso: barra flotante fija en la parte inferior, cuenta atrás en monoespaciada grande, editable con un toque. Amarillo mientras corre.

Cada ejercicio tiene un botón secundario **Ocupada** que abre una hoja inferior con las alternativas del mismo patrón de movimiento, cada una con su imagen.

### 3. Detalle de ejercicio
Imagen grande arriba, nombre, y una explicación en dos o tres frases en lenguaje llano de qué es y qué músculo trabaja. Debajo, el historial de pesos de ese ejercicio con la barra cargada y una línea de tendencia sobria.

### 4. Historial
Sesiones pasadas en lista. Arriba, adherencia de las últimas cuatro semanas como una cifra honesta y una cuadrícula de sesiones hechas. Sin rachas de fuego, sin insignias, sin confeti.

Debajo, gráfica de peso corporal con media móvil de 7 días.

### 5. Rutina
Las cinco sesiones y sus ejercicios, editables y reordenables.

### 6. Ajustes
Perfil, cambio de usuario, tiempos de descanso por defecto, exportar datos.

---

## Imágenes

Usa marcadores de posición ahora, pero define el tratamiento, porque las fotos reales vendrán de fuentes distintas y hay que unificarlas:

- **Miniatura en lista**: cuadrada, 64 × 64, radio 8 px.
- **Cabecera de detalle**: 4:3, ancho completo.
- **Tratamiento**: duotono tinta sobre cemento, usando los mismos dos colores de la paleta. Es lo que hace que veinte fotos de stock distintas parezcan una sola colección.
- El sujeto siempre centrado y a la misma escala relativa, en el punto medio del movimiento.

---

## Microinteracciones

Pocas y funcionales.

- Marcar serie: la fila se rellena de verde de izquierda a derecha en 180 ms.
- Cronómetro de descanso: al llegar a cero, un pulso corto del contenedor y vibración. Nada de sonido por defecto.
- Sustituir ejercicio: la miniatura hace un cambio cruzado, la tarjeta mantiene su posición.
- Progresión sugerida: cuando la app propone subir peso, el disco nuevo de la barra cargada entra deslizándose. Es la única celebración que tiene la app, y celebra un dato real.

Respeta `prefers-reduced-motion`.

---

## Voz de la interfaz

Español de España, en minúscula de frase, verbos activos, sin signos de exclamación y sin emojis. La app no anima, informa.

- Botones: "Empezar", "Terminar sesión", "Ocupada", "Saltar esta sesión".
- Estado vacío del historial: "Aún no hay sesiones registradas. La primera aparecerá aquí en cuanto termines una."
- Sugerencia de progresión: "La última vez completaste las 4 series a 8 repeticiones. Prueba con 2,5 kg más."
- Aviso de recuperación: "Llevas tres días seguidos entrenando. Descansar también forma parte del plan."

---

## Qué evitar explícitamente

- Gamificación: rachas con llamas, medallas, niveles, confeti.
- Degradados de color, glassmorphism, sombras difusas grandes.
- Iconos genéricos de mancuerna como relleno donde debería ir la foto real del ejercicio.
- Menús de navegación con más de cuatro destinos.
- Cualquier cosa que requiera dos manos o precisión fina.
