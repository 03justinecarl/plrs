// Quiz Countdown Timer
function startTimer(seconds, displayId, formId) {
  const display = document.getElementById(displayId);
  const form = document.getElementById(formId);
  let remaining = seconds;

  function update() {
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    display.textContent = `${m}:${s.toString().padStart(2, '0')}`;
    if (remaining <= 30) display.parentElement.classList.add('danger');
    if (remaining <= 0) {
      display.textContent = '0:00';
      form.submit();
      return;
    }
    remaining--;
    setTimeout(update, 1000);
  }
  update();
}
