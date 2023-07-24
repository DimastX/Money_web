function check() {
  if (document.getElementById("SMD").checked) {
    document.getElementById("SMD_off").classList.remove('disable_section')
  } else {
    document.getElementById("SMD_off").classList.add('disable_section')
  }
}