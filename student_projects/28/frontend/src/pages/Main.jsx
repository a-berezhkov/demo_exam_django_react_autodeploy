import React, { useEffect, useState } from 'react'
import BookCard from '../components/BookCard'
import Loader from '../components/Loader'
function Main() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const getBooks = async () => {
    const resp = await fetch(import.meta.env.VITE_URL + "books/")
    const json = await resp.json()
     if (resp.ok) {
      setBooks(json.data)
      
    }
    setLoading(false)
  }

  useEffect(()=>{
    getBooks()
  },[])

  return (
    <div className='page'>
      <div className="center">
        <h1>Каталог</h1>
        {
          loading && <Loader></Loader>
        }
        {
          books.map(el=>(
            <BookCard book={el}></BookCard>
          ))
        } {
          books.length == 0 && <h3>Тут ничего нет</h3>
        }
      </div>
    </div>
  )
}

export default Main
