void heateqn(int* a, int m, int n){
  int i;
  int j;
  for(i = 0; i < n; i++){
   for(j = 1; j < n; j++) {
       a[j] = a[j + 1] + a[j-1];
   }
}
}