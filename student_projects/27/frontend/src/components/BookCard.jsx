import React, {useState} from 'react'

function BookCard({book}) {
  const [loading, setLoading] = useState(false)
  const onDown = async () => {
    setLoading(true)
    const resp = await fetch(`http://localhost:8000/api/books/${book.id}/download`, {
      'method': 'POST',
      'headers': {
        'Authorization': 'Bearer '+ localStorage.getItem('token')
      }
    })
    if (resp.ok) {
      setLoading(false)
      const toast = document.createElement('div');
      toast.classList.add('toast');
      toast.textContent = 'Книга сохранена в вашей истории!';
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.remove();
      }, 3000);
    }

  }

  return (
    <div className='card'>
        <h3>Название: {book.title}</h3>
        <p> Автор:{book.author}</p>
        <p>Категория: {book.category.name}</p>
        <img className='imagebook' src={book.cover} alt="img" />
        <button onClick={()=>onDown()}>Загрузить</button>
    </div>
  )
}

export default BookCard
