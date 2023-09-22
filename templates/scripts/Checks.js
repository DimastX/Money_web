function check(master_box, slave) {
    if (document.getElementById(master_box).checked) {
      document.getElementById(slave).classList.remove('disable_section')
    } else {
      document.getElementById(slave).classList.add('disable_section')
    }
  }