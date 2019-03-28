def missing_elements(L, start, end):
    if end - start <= 1: 
        if L[end] - L[start] > 1:
            yield from range(L[start] + 1, L[end])
        return

    index = start + (end - start) // 2
    print("index " + str(index))
    # is the lower half consecutive?
    consecutive_low =  L[index] == L[start] + (index - start)
    if not consecutive_low:
        yield from missing_elements(L, start, index)

    # is the upper part consecutive?
    consecutive_high =  L[index] == L[end] - (end - index)
    if not consecutive_high:
        yield from missing_elements(L, index, end)

def hasduplicate(serialNolist):
    serialNolist.sort()
    print(serialNolist)
    
    new_list = sorted(set(serialNolist))
    dup_list =[]
    
    for i in range(len(new_list)):
            if (serialNolist.count(new_list[i]) > 1 ):
                dup_list.append(new_list[i])
    print(dup_list)

def missing_numbers(num_list):
      original_list = [x for x in range(num_list[0], num_list[-1] + 1)]
      num_list = set(num_list)
      return (list(num_list ^ set(original_list)))

def main():
    L = [10,11,13,14,14,15,16,17,19,20]
    print(missing_numbers(L))
    #print(list(missing_elements(L,0,len(L)-1)))
    #L = [10,11,13,13,14,15,16,17,18,19,20]
    hasduplicate(L)
    
main()