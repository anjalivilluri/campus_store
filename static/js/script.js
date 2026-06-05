document.addEventListener("DOMContentLoaded",()=>{

    const cards=
    document.querySelectorAll(".card");

    cards.forEach((card,index)=>{

        card.style.opacity="0";

        setTimeout(()=>{

            card.style.opacity="1";
            card.classList.add("fade-in");

        },index*150);

    });

});