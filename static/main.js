document.addEventListener('DOMContentLoaded', () => {
            
    document.querySelectorAll('.showContentBtn').forEach(button => {
        
        button.onclick = showContent;
    });
    
    if (document.querySelector('#ratingSelect')) {

        document.querySelector('#ratingSelect').onclick = displaySelectedRating;
    }

    if (document.querySelector('#editReviewBtn')) {

        document.querySelector('#editReviewBtn').onclick = showEditReview;
    }
});

 function showContent() {

    this.style.display = 'none';
    document.querySelectorAll(`.${this.dataset.showgroup}`).forEach(item => {

        item.style.display = 'initial';
    });
    document.querySelector(`#${this.dataset.showgroup}-focus`).focus();
}

function isOverflown(element) {

    return element.scrollHeight > element.clientHeight || element.scrollwidth > element.clientWidth;
}

let reviews = document.querySelectorAll('.review')
if (reviews) {
    
    reviews.forEach(review => {

        let reviewMoreBtn = review.querySelector('.reviewMoreBtn');
        reviewMoreBtn.style.display = (isOverflown(review) ? 'initial' : 'none');
        reviewMoreBtn.onclick = function() {

            this.closest('.review').style.height = 'auto';
            this.style.display = 'none';
        };
    });
}


// book profile

let newReviewBtn = document.querySelector('#newReviewBtn');
let showNewReviewForm = document.querySelector('#showNewReviewForm');
let newReviewForm = document.querySelector('#newReviewForm');
let showRating = document.querySelector('#showRating');
let editReviewForm = document.querySelector('#editReviewForm');

if (newReviewBtn) {

    newReviewBtn.onclick = () => {

        newReviewBtn.style.display = 'none';
        showNewReviewForm.style.display = 'initial';
    }
}

function displaySelectedRating() {

    setTimeout(() => { showRating.innerHTML = document.querySelector('input[name="rating"]:checked').value; }, 50);

}

function showEditReview() {

    // fetch original rating value
    let oldRating = showRating.innerHTML;

    document.querySelector('#editReviewBtn').style.display = 'none';
    document.querySelector('#currentReviewInfo').style.display = 'none';
    // set default rating value to original rating value
    document.querySelector(`input[value="${oldRating}"]`).setAttribute('checked', true);
    editReviewForm.style.display = 'initial';
    setTimeout(() => { document.querySelector('#submitEditBtn').removeAttribute('disabled'); }, 1500)
}

function validateForm() {

    if (!document.querySelector('input[name="rating"]:checked')) {

        alert('Please select a rating')
        return false;
    }

    return true;
}

if (newReviewForm) {

    newReviewForm.onsubmit = validateForm;
}

if (editReviewForm) {

    editReviewForm.onsubmit = validateForm;
}
