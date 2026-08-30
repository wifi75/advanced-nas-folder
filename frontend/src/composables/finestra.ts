import { onBeforeUnmount, onMounted, type Ref } from 'vue'

/**
 * Chiude una finestra con Esc.
 *
 * Prima si chiudevano anche cliccando sullo sfondo, e un clic di troppo faceva
 * perdere quello che si stava scrivendo — un modulo compilato a metà sparisce
 * senza che sia chiaro cosa sia successo. Chiudere è ora una cosa che si fa
 * apposta: Esc, oppure il pulsante Annulla.
 *
 * @param aperta  vero quando la finestra è a schermo
 * @param chiudi  cosa fare per chiuderla
 */
export function chiudiConEsc(aperta: Ref<boolean> | (() => boolean), chiudi: () => void): void {
  const eAperta = (): boolean => (typeof aperta === 'function' ? aperta() : aperta.value)

  function alTasto(evento: KeyboardEvent): void {
    if (evento.key !== 'Escape' || !eAperta()) return
    // Ferma la propagazione: con due finestre sovrapposte — la conferma di
    // eliminazione sopra un dettaglio — un solo Esc le chiuderebbe entrambe.
    evento.stopPropagation()
    chiudi()
  }

  // Sull'elemento della pagina e non sulla finestra del browser: così l'ordine
  // di ascolto segue quello dei componenti, e la finestra più interna risponde
  // per prima.
  onMounted(() => document.addEventListener('keydown', alTasto))
  onBeforeUnmount(() => document.removeEventListener('keydown', alTasto))
}
