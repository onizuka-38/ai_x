class Student{
  constructor(name, kor, mat, eng, sci){
    this.name = name;
    this.kor  = kor;
    this.mat  = mat;
    this.eng  = eng;
    this.sci  = sci;
  }
  getSum(){
    return this.kor + this.mat + this.eng + this.sci;
  }
  getAvg(){
    return this.getSum() / 4;
  }
  toString(){
    return '이름:'+this.name +
          ' 국어:'+this.kor +
          ' 수학:'+this.mat +
          ' 영어:'+this.eng +
          ' 과학:'+this.sci +
          ' 합:'+this.getSum() +
          ' 평균:'+this.getAvg();
  }
}//class
var hong = new Student("홍", 100, 100, 99, 100);
console.log(hong.toString());
console.log(`${hong}`);
console.log(hong);