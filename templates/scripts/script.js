// Функция для фильтрации списка директорий на стороне клиента.
function filterDirectories() {
    // Получение элемента поля ввода для поиска.
    var input = document.getElementById("search");
    // Получение значения фильтра из поля ввода и приведение его к нижнему регистру для регистронезависимого поиска.
    var filter = input.value.toLowerCase();
    // Получение элемента списка директорий.
    var directoryList = document.getElementById("directory-list");
    // Получение всех элементов списка директорий (предполагается, что они имеют класс "directory-item").
    var directoryItems = directoryList.getElementsByClassName("directory-item");
    
    // Итерация по каждому элементу списка директорий.
    for (var i = 0; i < directoryItems.length; i++) {
      // Получение первого тега <p> внутри текущего элемента списка (предполагается, что имя директории находится там).
      var directoryName = directoryItems[i].getElementsByTagName("p")[0];
      
      // Проверка, содержит ли имя директории (в нижнем регистре) текст фильтра.
      if (directoryName.innerText.toLowerCase().indexOf(filter) > -1) {
        // Если содержит, элемент отображается.
        directoryItems[i].style.display = "";
      } else {
        // Если не содержит, элемент скрывается.
        directoryItems[i].style.display = "none";
      }
    }
  }
  
  // Назначение функции filterDirectories в качестве обработчика события "keyup" для поля ввода с ID "search".
  // Это означает, что фильтрация будет происходить по мере ввода текста пользователем.
  document.getElementById("search").addEventListener("keyup", filterDirectories);