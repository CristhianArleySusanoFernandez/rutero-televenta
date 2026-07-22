# 📋 Manual de la Asesora — Rutero Televenta

**Distribuciones Santiago De Tunja S.A.S**

Este manual explica cómo usar el sistema de televenta paso a paso.
Imprímalo y déjelo al lado del computador.

---

## 1. Cada mañana: encender el sistema

1. En la carpeta del programa, haga **doble clic en `INICIAR.bat`**.
2. Se abre una **ventana negra** con letras. Esa ventana es el sistema funcionando.
   **NO LA CIERRE.** Si la cierra, todo se apaga.
3. Espere unos segundos: el navegador se abre solo con la página del rutero.
4. En la ventana negra aparece un recuadro que dice:

   ```
   ESCRIBE ESTA DIRECCION EN LA APP DEL TELEFONO:
   ws://192.168.X.X:8000/ws/telefono
   ```

   **Anote o mire esa dirección** — la va a necesitar en el paso siguiente.
   ⚠️ Esta dirección **puede cambiar de un día para otro**. Mírela cada mañana.

> 💡 La ventana negra puede quedar minimizada (botón −), pero **nunca cerrada** (botón ✕).

---

## 2. Conectar el teléfono

1. Tome el teléfono de la empresa y **abra la app de llamadas del rutero**.
2. Compare la dirección que muestra la app con la que salió en la ventana negra.
   - ¿Es la misma? Siga al paso 3.
   - ¿Es diferente? Bórrela y **escriba la que dice la ventana negra de HOY**.
3. Pulse **Conectar** en la app.
4. Mire la página del rutero en el computador, arriba a la derecha hay un aviso (badge):
   - 🟢 **"📱 ... listo"** en verde → todo bien, puede trabajar.
   - 🔴 **"📵 Sin teléfono conectado"** en rojo → algo falló. Vaya a la sección
     **8. Problemas frecuentes**.

### ⚠️ MUY IMPORTANTE: la app debe quedar abierta TODO el día

- Deje el teléfono con la **app abierta y visible en la pantalla**, conectado al cargador.
- Si **cierra la app** o la **deja en segundo plano** (se pone a usar WhatsApp, la cámara,
  etc.), el teléfono se desconecta y el botón "Llamar" del computador **deja de funcionar**.
- El teléfono y el computador deben estar en la **misma red WiFi** de la oficina.

---

## 3. Cargar el rutero del día

1. En la página del rutero, pulse **📂 Cargar Rutero**.
2. Elija el archivo **Excel** con los clientes del día.
3. Espere a que aparezca la lista de clientes con el contador arriba
   (Total, Contestó, No contestó, etc.).

Si el rutero ya estaba cargado (por ejemplo, después de reiniciar el computador),
la lista aparece sola. No hace falta cargarlo dos veces.

---

## 4. Trabajar la cola de llamadas

1. Pulse **▶ Iniciar cola**. El sistema le muestra **un cliente a la vez**, en orden.
2. **ANTES de llamar, lea la tarjeta del cliente:**
   - Las **📌 Notas permanentes** (recuadro amarillo arriba): instrucciones especiales
     de ese cliente. Ejemplo: *"solo ofrecer galletas"*.
   - El **historial** (abajo): lo que pasó en llamadas anteriores.
   - Los avisos: si dice **⏰ Reagendado**, el cliente pidió que lo volvieran a llamar.
3. Pulse **📞 Llamar**. El teléfono **marca solo** — usted no tiene que digitar el número.
4. Hable con el cliente por el teléfono, como una llamada normal.
5. Al terminar, **cuelgue desde el teléfono**.
6. En el computador, marque el resultado:

   | Botón | Cuándo usarlo |
   |---|---|
   | ✓ **Contestó** (verde) | Habló con el cliente y quedó todo bien |
   | ✗ **No contestó** (rojo) | Timbró y nadie contestó. El sistema lo vuelve a intentar más tarde una vez |
   | ⚠ **Registrar novedad** | Pasó algo especial: negocio cerrado, cambió de dueño, número equivocado, no quiere que lo llamen, etc. |
   | ⏰ **Reagendar** | El cliente contestó pero pidió que lo llamen más tarde (elija 10 min, 30 min, 1 hora o un tiempo a su gusto) |
   | ⏭ **Saltar** | El número es inválido o no se puede llamar a ese cliente |

7. Al marcar el resultado, el sistema pasa **solo** al siguiente cliente. Repita desde el paso 2.
8. Si necesita parar un momento (baño, almuerzo), pulse **⏸ Pausar**: el sistema termina
   con el cliente actual y no le muestra más hasta que vuelva a pulsar **▶ Iniciar cola**.

---

## 5. Novedad vs. Nota permanente — NO son lo mismo

Esto confunde al principio. La regla:

| | ⚠ NOVEDAD | 📌 NOTA PERMANENTE |
|---|---|---|
| **Qué es** | Lo que pasó **en esta llamada de hoy** | Una instrucción sobre el cliente que aplica **siempre** |
| **Dónde se ve después** | En el **historial** del cliente | En el recuadro **amarillo de arriba**, cada vez que salga ese cliente |
| **Ejemplos** | "No contestó", "Negocio cerrado", "Cambió de dueño", "Número equivocado" | "Solo ofrecer galletas", "Llamar siempre después de las 10 am", "Hablar con doña Marta, no con el esposo" |

**Forma fácil de decidir:**

- ¿Está contando **qué pasó hoy**? → es una **Novedad** (botón ⚠ Registrar novedad).
- ¿Es algo que la próxima asesora **debe saber antes de llamar**, hoy y siempre?
  → es una **Nota permanente** (botón **+ Agregar nota** en el recuadro amarillo).

Ejemplo completo: el cliente contesta y dice *"no me ofrezcan más gaseosa, solo pido
galletas"*. Eso va como **nota permanente** ("solo ofrecer galletas"), porque aplica
para todas las llamadas futuras. Y la llamada de hoy se marca **✓ Contestó**.

---

## 6. Clientes reagendados: la pantalla de espera

Cuando ya llamó a todos y **solo faltan los reagendados** (los que pidieron que los
llamaran más tarde), aparece una pantalla que dice **"Queda(n) X cliente(s) reagendado(s)"**
con la lista y cuántos minutos faltan para cada uno.

- **No tiene que hacer nada**: la pantalla se actualiza sola cada 30 segundos y,
  cuando le llegue la hora a un cliente, el sistema se lo muestra automáticamente.
- **¿No puede esperar?** (por ejemplo, ya se acaba el turno): pulse
  **📞 Atender ahora** al lado del cliente. El sistema se lo muestra de una vez y
  le avisa con un recuadro que se estaba adelantando a la hora acordada.

Cuando termine con TODOS, sale **🎉 ¡Terminaste por hoy!**

---

## 7. Al final del día: exportar el reporte

1. Si está en la vista de llamadas, pulse **← Volver a la lista**.
2. Pulse **📊 Exportar reporte Excel**.
3. Se descarga un archivo Excel con el resultado de todas las llamadas del día.
4. Entregue o guarde ese archivo donde le indique su supervisor.
5. Ya puede cerrar la ventana negra (ahí sí, con la ✕) y apagar todo.

---

## 8. 🚨 PROBLEMAS FRECUENTES (síntoma → causa → solución)

### 🔴 El badge está rojo / dice "📵 Sin teléfono conectado"

**Causa:** el computador no encuentra el teléfono.
**Solución — revise en este orden:**

1. ¿La **app está abierta y visible** en el teléfono? Si está cerrada o minimizada, ábrala
   y pulse **Conectar** otra vez.
2. ¿La **dirección** en la app es la misma que muestra la **ventana negra de hoy**?
   La IP puede cambiar de un día para otro. Corríjala y pulse Conectar.
3. ¿El teléfono está en la **misma WiFi** que el computador? Revise que no se haya pasado
   a datos móviles o a otra red. Conéctelo a la WiFi de la oficina.
4. Si nada funciona: cierre la app del todo, ábrala de nuevo, y pulse Conectar.

### 📵 El teléfono estaba bien y se desconectó solo a media mañana

**Causa:** el teléfono "durmió" la app para ahorrar batería.
**Solución:**

1. Abra la app otra vez y pulse **Conectar** — con eso vuelve a funcionar de inmediato.
2. Para que no vuelva a pasar: deje el teléfono **conectado al cargador** y con la
   **app en pantalla** (no la minimice). Pida que le desactiven la *optimización de
   batería* para esta app (Ajustes → Batería → la app → Sin restricciones).

### 📞 Pulso "Llamar" y sale "teléfono ocupado"

**Causa:** el teléfono todavía está en una llamada (o cree que lo está).
**Solución:**

1. Mire el teléfono: si hay una llamada activa, **cuélguela** primero.
2. Espere a que el badge vuelva a verde ("listo") y pulse **Llamar** de nuevo.

### ⬛ La ventana negra se cerró (o alguien la cerró sin querer)

**Causa:** al cerrarse esa ventana, el sistema completo se apaga. Por eso el navegador
dice que no puede mostrar la página y el teléfono se desconecta.
**Solución:**

1. Doble clic en **INICIAR.bat** otra vez.
2. Espere a que abra el navegador.
3. Vuelva a conectar el teléfono (sección 2) — revise la IP, pudo cambiar.
4. El trabajo **no se pierde**: los clientes ya llamados quedan guardados.

### 🛡️ Windows preguntó "¿Permitir acceso?" (Firewall)

**Causa:** la primera vez, Windows pide permiso para que el teléfono se conecte al computador.
**Solución:** pulse **Permitir acceso**. Si le dieron "Cancelar" por error, el teléfono
nunca va a poder conectarse — pida ayuda a soporte para habilitarlo en el Firewall.

### 📵 En la tarjeta del cliente sale "Teléfono inválido o faltante"

**Causa:** el número de ese cliente está mal escrito o vacío en el Excel.
**Solución:** pulse **⏭ Saltar (número inválido)**. Queda registrado y el sistema
sigue con el siguiente. Avise para que corrijan el número en la base.

---

## Resumen de un vistazo

```
MAÑANA:   INICIAR.bat → mirar IP en ventana negra → conectar app del teléfono
          → badge verde → cargar Excel → ▶ Iniciar cola

POR CADA CLIENTE:   leer notas → 📞 Llamar → hablar → colgar → marcar resultado

TARDE:    esperar reagendados (o "Atender ahora") → 🎉 Terminaste
          → 📊 Exportar reporte Excel → cerrar
```

**Las 3 reglas de oro:**

1. La **ventana negra nunca se cierra** durante el día.
2. La **app del teléfono siempre abierta y visible**, con cargador.
3. **Leer las notas permanentes ANTES de llamar.**
