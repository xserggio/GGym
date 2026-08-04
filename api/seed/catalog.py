"""Shared exercise catalogue (spec §8).

Each entry is (name, pattern, equipment, description). `default_rest_s` is not
stored here: it is derived by `default_rest_s()` from the spec rule
"90 accesorios, 120 pesados" — 120 s for compound patterns performed with a
barbell or bodyweight, 90 s otherwise. A routine can still override per exercise
via `routine_day_exercises.rest_s`.

Names are the catalogue's natural key and must be unique. Routine exercises and
their alternatives live in the same list; the routine template references these
names verbatim.
"""
from __future__ import annotations

from app.models.enums import Equipment as EQ
from app.models.enums import MovementPattern as MP

# Compound patterns that warrant the longer 120 s rest when loaded with a
# barbell or bodyweight.
_COMPOUND = {
    MP.empuje_horizontal,
    MP.empuje_vertical,
    MP.tiron_horizontal,
    MP.tiron_vertical,
    MP.cuadriceps,
    MP.cadena_posterior,
    MP.gluteo,
}
_HEAVY_EQUIPMENT = {EQ.barra, EQ.peso_corporal}


def default_rest_s(pattern: MP, equipment: EQ) -> int:
    if pattern in _COMPOUND and equipment in _HEAVY_EQUIPMENT:
        return 120
    return 90


# (name, pattern, equipment, description)
CATALOG: list[tuple[str, MP, EQ, str]] = [
    # --- empuje_horizontal ---
    ("Press banca", MP.empuje_horizontal, EQ.barra,
     "Tumbado en banco, empujas la barra desde el pecho hasta extender los brazos. Trabaja pectoral, hombro anterior y tríceps."),
    ("Press inclinado con mancuernas", MP.empuje_horizontal, EQ.mancuernas,
     "Como el press de banca pero con el banco inclinado y mancuernas, incide más en la parte alta del pectoral."),
    ("Cruces en polea", MP.empuje_horizontal, EQ.polea,
     "De pie entre dos poleas, juntas las manos al frente en arco. Aísla el pectoral con poca carga en el hombro."),
    ("Press banca con mancuernas", MP.empuje_horizontal, EQ.mancuernas,
     "Versión del press de banca con mancuernas, que permite más recorrido y equilibra ambos lados."),
    ("Press de pecho en máquina", MP.empuje_horizontal, EQ.maquina,
     "Empuje horizontal guiado por máquina. Aísla el pectoral con la espalda apoyada, útil para acumular volumen seguro."),
    ("Fondos en paralelas", MP.empuje_horizontal, EQ.peso_corporal,
     "Suspendido en paralelas, bajas y subes el cuerpo. Trabaja pectoral bajo y tríceps con tu propio peso."),
    ("Pec deck", MP.empuje_horizontal, EQ.maquina,
     "Sentado en máquina, juntas los brazos al frente. Aísla el pectoral en un recorrido fijo."),

    # --- empuje_vertical ---
    ("Press militar de pie", MP.empuje_vertical, EQ.barra,
     "De pie, empujas la barra por encima de la cabeza. Trabaja hombro y tríceps y exige estabilidad de core."),
    ("Press de hombro en máquina", MP.empuje_vertical, EQ.maquina,
     "Empuje vertical guiado por máquina. Trabaja el deltoides con la espalda apoyada."),
    ("Press militar con mancuernas", MP.empuje_vertical, EQ.mancuernas,
     "Press de hombro sentado o de pie con mancuernas, con más recorrido que la barra."),
    ("Press Arnold", MP.empuje_vertical, EQ.mancuernas,
     "Press de hombro con giro de muñeca durante la subida. Incide en la cabeza anterior y media del deltoides."),

    # --- tiron_horizontal ---
    ("Remo con barra", MP.tiron_horizontal, EQ.barra,
     "Inclinado con la espalda recta, tiras de la barra hacia el abdomen. Trabaja dorsal, romboides y trapecio."),
    ("Remo sentado en polea", MP.tiron_horizontal, EQ.polea,
     "Sentado, tiras del agarre hacia el abdomen. Trabaja la espalda media con recorrido controlado."),
    ("Remo en máquina con pecho apoyado", MP.tiron_horizontal, EQ.maquina,
     "Con el pecho apoyado, tiras de los brazos hacia atrás. Aísla la espalda sin cargar la zona lumbar."),
    ("Face pull", MP.tiron_horizontal, EQ.polea,
     "Tiras de una cuerda hacia la cara con los codos altos. Trabaja deltoides posterior y salud del hombro."),
    ("Remo T", MP.tiron_horizontal, EQ.barra,
     "Remo con un extremo de la barra anclado, agarre en V. Carga la espalda media con la torso apoyado o inclinado."),
    ("Remo con mancuerna a una mano", MP.tiron_horizontal, EQ.mancuernas,
     "Apoyado en un banco, remas con una mancuerna. Trabaja cada lado de la espalda por separado."),
    ("Remo en máquina", MP.tiron_horizontal, EQ.maquina,
     "Remo horizontal guiado por máquina. Recorrido fijo para la espalda media."),
    ("Remo en polea agarre ancho", MP.tiron_horizontal, EQ.polea,
     "Remo sentado con agarre ancho, incide más en la espalda alta y el deltoides posterior."),

    # --- tiron_vertical ---
    ("Jalón agarre neutro", MP.tiron_vertical, EQ.polea,
     "Sentado, tiras de la barra hacia el pecho con agarre neutro. Trabaja el dorsal con menos tensión en el hombro."),
    ("Dominadas", MP.tiron_vertical, EQ.peso_corporal,
     "Colgado de una barra, subes hasta pasar la barbilla. Trabaja dorsal y bíceps con tu propio peso."),
    ("Jalón agarre ancho", MP.tiron_vertical, EQ.polea,
     "Jalón al pecho con agarre ancho, enfatiza la anchura del dorsal."),
    ("Dominadas asistidas", MP.tiron_vertical, EQ.maquina,
     "Dominada con ayuda de una máquina que contrarresta parte del peso. Progresión hacia la dominada libre."),
    ("Pullover en polea", MP.tiron_vertical, EQ.polea,
     "De pie, llevas la barra desde arriba hasta los muslos con los brazos casi rectos. Aísla el dorsal."),

    # --- cuadriceps ---
    ("Sentadilla", MP.cuadriceps, EQ.barra,
     "Con la barra a la espalda, flexionas rodillas y caderas y subes. Ejercicio base para cuádriceps y glúteo."),
    ("Prensa", MP.cuadriceps, EQ.maquina,
     "Empujas una plataforma con las piernas desde una posición sentada. Carga el cuádriceps sin exigir equilibrio."),
    ("Hack squat", MP.cuadriceps, EQ.maquina,
     "Sentadilla guiada en máquina inclinada. Aísla el cuádriceps con la espalda apoyada."),
    ("Sentadilla búlgara", MP.cuadriceps, EQ.mancuernas,
     "Sentadilla a una pierna con el pie trasero elevado. Trabaja cuádriceps y glúteo de cada pierna por separado."),
    ("Extensión de cuádriceps", MP.cuadriceps, EQ.maquina,
     "Sentado, extiendes las rodillas contra una palanca. Aísla el cuádriceps."),
    ("Sentadilla frontal", MP.cuadriceps, EQ.barra,
     "Sentadilla con la barra apoyada delante, sobre los hombros. Exige más al cuádriceps y a la postura erguida."),
    ("Sentadilla en multipower", MP.cuadriceps, EQ.maquina,
     "Sentadilla con la barra guiada en raíles. Más estable, útil para cargar seguro sin compañero."),
    ("Zancadas caminando", MP.cuadriceps, EQ.mancuernas,
     "Avanzas dando zancadas largas con mancuernas. Trabaja cuádriceps y glúteo de forma unilateral."),
    ("Sentadilla goblet", MP.cuadriceps, EQ.mancuernas,
     "Sentadilla sujetando una mancuerna contra el pecho. Enseña un patrón limpio con carga moderada."),

    # --- cadena_posterior ---
    ("Peso muerto rumano", MP.cadena_posterior, EQ.barra,
     "Con las piernas casi rectas, bajas la barra pegada a las piernas y subes con la cadera. Trabaja femoral y glúteo."),
    ("Curl femoral tumbado", MP.cadena_posterior, EQ.maquina,
     "Tumbado boca abajo, flexionas las rodillas contra una palanca. Aísla el femoral."),
    ("Curl femoral sentado", MP.cadena_posterior, EQ.maquina,
     "Sentado, flexionas las rodillas contra una palanca. Aísla el femoral con la cadera flexionada."),
    ("Peso muerto rumano con mancuernas", MP.cadena_posterior, EQ.mancuernas,
     "Como el rumano con barra pero con mancuernas, con más recorrido y libertad en las manos."),
    ("Buenos días", MP.cadena_posterior, EQ.barra,
     "Con la barra a la espalda, inclinas el tronco al frente con las piernas casi rectas. Trabaja femoral y lumbar."),
    ("Curl femoral de pie", MP.cadena_posterior, EQ.maquina,
     "De pie, flexionas una rodilla contra una palanca. Aísla el femoral de cada pierna."),
    ("Hiperextensiones", MP.cadena_posterior, EQ.peso_corporal,
     "Sobre un banco a 45 grados, subes el tronco desde la flexión de cadera. Trabaja lumbar, glúteo y femoral."),

    # --- gluteo ---
    ("Hip thrust", MP.gluteo, EQ.barra,
     "Con la espalda apoyada en un banco y la barra en la cadera, empujas hacia arriba. Ejercicio base de glúteo."),
    ("Hip thrust en máquina", MP.gluteo, EQ.maquina,
     "Empuje de cadera guiado por máquina. Aísla el glúteo con carga cómoda de ajustar."),
    ("Patada de glúteo en polea", MP.gluteo, EQ.polea,
     "De pie, llevas una pierna hacia atrás contra la polea. Aísla el glúteo de cada lado."),
    ("Puente de glúteo", MP.gluteo, EQ.peso_corporal,
     "Tumbado, elevas la cadera apretando el glúteo. Versión sencilla del empuje de cadera, sin material."),

    # --- gemelo ---
    ("Gemelos de pie", MP.gemelo, EQ.maquina,
     "De pie, elevas los talones contra una carga. Trabaja el gemelo en su rango completo."),

    # --- deltoides_lateral ---
    ("Elevaciones laterales en polea", MP.deltoides_lateral, EQ.polea,
     "Subes el brazo lateralmente contra la polea. Aísla la cabeza lateral del deltoides con tensión constante."),
    ("Elevaciones laterales con mancuernas", MP.deltoides_lateral, EQ.mancuernas,
     "Subes las mancuernas hacia los lados hasta la altura de los hombros. Aísla el deltoides lateral."),

    # --- triceps ---
    ("Tríceps en polea", MP.triceps, EQ.polea,
     "De pie, extiendes los codos empujando la barra hacia abajo. Aísla el tríceps."),
    ("Press francés", MP.triceps, EQ.barra,
     "Tumbado, bajas la barra hacia la frente flexionando solo los codos. Aísla el tríceps."),
    ("Fondos en banco", MP.triceps, EQ.peso_corporal,
     "Con las manos en un banco detrás, bajas y subes el cuerpo. Trabaja el tríceps con tu peso."),
    ("Extensión sobre la cabeza en polea", MP.triceps, EQ.polea,
     "Extiendes los brazos por encima de la cabeza contra la polea. Incide en la cabeza larga del tríceps."),

    # --- biceps ---
    ("Curl con barra Z", MP.biceps, EQ.barra,
     "De pie, flexionas los codos subiendo la barra Z. El agarre inclinado cuida las muñecas. Trabaja el bíceps."),
    ("Curl martillo", MP.biceps, EQ.mancuernas,
     "Curl con agarre neutro, las palmas enfrentadas. Trabaja bíceps y braquial."),
    ("Curl con mancuernas", MP.biceps, EQ.mancuernas,
     "Flexionas los codos subiendo las mancuernas. Trabajo básico de bíceps, alternando o a la vez."),
    ("Curl en banco inclinado", MP.biceps, EQ.mancuernas,
     "Curl sentado en banco inclinado, con los brazos por detrás del cuerpo. Estira más la cabeza larga del bíceps."),
    ("Curl en polea baja", MP.biceps, EQ.polea,
     "Curl de pie contra la polea baja, con tensión constante en todo el recorrido."),

    # --- core ---
    ("Rueda abdominal", MP.core, EQ.peso_corporal,
     "De rodillas, ruedas una rueda hacia delante y vuelves sin arquear la espalda. Exige mucho al core."),
    ("Elevaciones de piernas colgado", MP.core, EQ.peso_corporal,
     "Colgado de una barra, subes las piernas al frente. Trabaja el abdomen inferior."),
    ("Plancha", MP.core, EQ.peso_corporal,
     "Aguantas el cuerpo recto apoyado en antebrazos y pies. Trabaja el core de forma isométrica."),
    ("Crunch en polea", MP.core, EQ.polea,
     "De rodillas, flexionas el tronco hacia abajo contra la polea. Trabaja el recto abdominal con carga."),
]
