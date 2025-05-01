def splitArray(nums, k):
    # nums.sort()
    nums_sum = sum(nums)

    def check_if_poss(nums, k, largest_sum):
        """
        Check if it's possible to split the array into at most k subarrays 
        such that the sum of each subarray does not exceed largest_sum.
        """
        sub_arrays = 1  # Start with one subarray
        sum_counter = 0

        for num in nums:
            if num > largest_sum:
                return False  # A single number exceeds largest_sum — not possible

            if sum_counter + num > largest_sum:
                # Start a new subarray
                sub_arrays += 1
                sum_counter = num
            else:
                sum_counter += num

        return sub_arrays <= k
    
    low = nums_sum//k
    high = nums_sum
    while low <= high:
        mid = low + (high - low)//2
        print(f"checking for mid = {mid}")
        if check_if_poss(nums, k, mid):
            print(f"possible for largest sum = {mid}")
            high = mid - 1
        else:
            print(f"\t not possible for {mid}")
            low = mid + 1
    return low
            

print(splitArray([7,2,5,10,8], 2))