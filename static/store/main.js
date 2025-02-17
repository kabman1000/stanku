
const categoriesDataBox = document.getElementById('cats-data-box')
const subcategoriesDataBox = document.getElementById('subcats-data-box')
const catInput = document.getElementById('cats')
const subcatInput = document.getElementById('subcats')
const subcatText = document.getElementById('subcat-text')
const catText = document.getElementById('cat-text')
const catForm = document.getElementById('cat-form')
const csrf = document.getElementsByName('csrfmiddlewaretoken')


$.ajax({
    type:'GET',
    url: '/category-json/',
    success: function(response){
        console.log(response.data)
        const categoriesData = response.data
        categoriesData.map(item => {
            const option = document.createElement('div')
            option.textContent = item.name
            option.setAttribute('class','item')
            option.setAttribute('data-value', item.name)
            categoriesDataBox.appendChild(option)
        })
    },
    error: function(error){
        console.log(error)
    }
})

catInput.addEventListener('change', e=>{
    console.log(e.target.value)
    const selectedCat = e.target.value

    subcategoriesDataBox.innerHTML = ""
    subcatText.textContent = "Choose a subcategory"
    subcatText.classList.add("default")

    $.ajax({
        type:'GET',
        url: `subcategory-json/${selectedCat}/`,
        success: function(response){
            console.log(response.data)
            const subcatsData = response.data
            subcatsData.map(item=>{
                const option = document.createElement('div')
                option.textContent = item.name
                option.setAttribute('class','item')
                option.setAttribute('data-value', item.name)
                subcategoriesDataBox.appendChild(option)
            })
        },
        error: function(response){
            console.log(error)
        }
    })
})

catForm.addEventListener('submit', e =>{
    $.ajax({
        type:'GET',
        url:'subcategory/',
        data:{
            'csrfmiddlewaretoken': csrf[0].value,
            'category': catText.textContent,
            'subcategory': subcatText.textContent,
        },
        success: function(response){
            console.log(response)
        },
        error: function(error){
            console.log(error)
        }
    })
    


})