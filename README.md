# bash
```
for item in rules skills commands; do
  ln -s $(realpath ./$item) ~/.cursor/$item
done
```
