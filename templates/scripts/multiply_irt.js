function updateResult(num1, num2, result) {
    const num1Input = document.getElementById("num1");
    const num2Input = document.getElementById("num2");
    const resultSpan = document.getElementById("result");

    const num1 = parseFloat(num1Input.value);
    const num2 = parseFloat(num2Input.value);
    const result = num1 * num2;
    resultSpan.textContent = result;
  }
