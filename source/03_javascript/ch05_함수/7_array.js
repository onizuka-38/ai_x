/* array함수 : 가변인자함수(파이썬에선 튜플매개변수)
 * 매개변수가 0개 : length가 0인 배열 생성 return
 * 매개변수가 1개 : length가 매개변수만큼의 크기인 배열 생성 return
 * 매개변수가 2개 이상 : 매개변수로 배열을 생성 return */
function array() {
  //arguments(매개변수 배열)에 매개변수 내용이 들어옴
  let result = [];
  if (arguments.length == 1) {
    // result를 arguments[0] 만큼의 크기인 배열
    for (var cnt = 1; cnt <= arguments[0]; cnt++) {
      result.push(null);
    }
  } else if (arguments.length >= 2) {
    // result를 arguments의 내용의 배열
    for (var idx = 0; idx < arguments.length; idx++) {
      result.push(arguments[idx]);
    }
  }
  return result;
}
var arr1 = array();
var arr2 = array(3);
var arr3 = array(1, 2, "삼");
console.log(arr1);
console.log(arr2);
console.log(arr3);
