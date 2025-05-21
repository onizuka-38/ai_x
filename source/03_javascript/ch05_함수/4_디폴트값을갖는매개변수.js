function pow(x = 1, y = 2) {
  //x의 y승을 return
  let result = 1;
  for (let cnt = 1; cnt <= y; cnt++) {
    result *= x; // result = result*x;
  }
  return result;
}
console.log(pow(3, 3));
