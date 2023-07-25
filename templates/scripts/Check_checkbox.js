function check(master, slave) {
  if (document.getElementById(master).checked) {
    document.getElementById(slave).classList.remove('disable_section')
  } else {
    document.getElementById(slave).classList.add('disable_section')
  }
}