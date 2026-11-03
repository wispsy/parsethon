// tongue: js
// JavaScript-style syntax demo in Parsethon
// Supports braces {}, semicolons ;, whitespace indifference, and JS vocabulary

function factorial(n) {
    if (n <= 1) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}

function calculate() {
    let numbers = [1, 2, 3, 4, 5];
    let total = 0;
    for (let x in numbers) {
        let f = factorial(x);
        console.log("Factorial of", x, "is", f);
        total = total + f;
    }
    return total;
}

let result = calculate();
console.log("Total sum:", result);
