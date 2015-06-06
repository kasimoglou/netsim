/**
  *	@file Basic runtime engine for generated vectorl code
  *	@author vsam
  *
  */


#ifndef _VECTORL_HH
#define _VECTORL_HH

#include <iostream>
#include <algorithm>
#include <array>

/**
	The namespace that contains language-related definitions.
  */
namespace vectorl
{

	//----------------------------------------------
	// 
	// Basic library for supporting expressions
	//
	//----------------------------------------------

	using namespace std;
	using namespace boost;


	namespace detail {

		/**
			 A recursive template definition for iterations
			 T is the element type of the index array
			 dims is the dimension of the index array
			 order is the recursion var.

			These classes are not meant to be used in user code.
			The multi_iteration template uses them.
		*/
		template <typename T, size_t dims, size_t order> struct iteration;

		/** 
			Base case: order-0.

			This is where all the index array as well as the extents
			array is stored.
		  */
		template <typename T, size_t dims> 
		struct iteration<T, dims, 0>
		{
			typedef std::array<T, dims> index_array;
			index_array __index;
			index_array __extent;

			inline bool advance() { return true; }
			inline index_array& index() { return __index; }
			inline const index_array& extent() const { return __extent; }

			inline iteration(const initializer_list<T>& ext) { reset(ext.begin(), ext.end()); }
			inline iteration(const index_array& ext) { reset(ext.begin(), ext.end()); }

			template <typename Iter>
			inline void reset(Iter from, Iter to) {				
				std::copy(from, to, __extent.begin());
				zero();
			}

			inline void zero() {
				for(T& x : __index) x=(T)0;				
			}

		};

		/**
			The recursive definition: iteration<T,d,n> is defined
			to contain an attribute of type iteration<T,d,n-1>.
		 */
		template <typename T, size_t dims, size_t order>
		struct iteration
		{
			typedef iteration<T, dims, order-1> sub_iteration;
			typedef typename sub_iteration::index_array index_array;

			sub_iteration subiter;   // a member of order one less

			inline index_array& index() { return subiter.index(); }	
			inline const index_array& extent() const { return subiter.extent(); }	

			inline T& __counter() { return index()[dims-order]; }
			inline const T& __size() { return extent()[dims-order]; }

			inline bool advance() {
				if(subiter.advance()) __counter()++;
				if(__counter()==__size()) {
					__counter() = (T)0;
					return true;
				}
				else
					return false;
			}

			template <typename Ext>
			iteration(const Ext& ext) : subiter(ext) {}

		};

	}

	/**
		An iteration object for multi-dimensional arrays.

		Instances of `multi_iteration<T, dims>` are initialized
		by a `dims`-sized array, \f$E\f$, of positive integers, called the
		extents.
		They also contain an index \f$I\f$, another `dims`-sized array.
		An iteration generates all values 
		   \f[ (0,\ldots,0) \leq I < E \f]
		in lexicographic order.

		For example, to iterate over all elements of a 3x4x2 `boost::multi_array`,
		you write:

			multi_array<double, 3> A { 3,4,2 };
			
			for(multi_iteration<index,3> I {{3,4,2}};  I;  ++I) {
				A(*I) = 0.0; // or something
			 }
		
		Of course, there are other uses for multi_iteration, aside from
		indexing arrays.
	  */
	template <typename T, size_t dims>
	class multi_iteration : detail::iteration<T, dims, dims>
	{
	private:
		bool finished;
		typedef detail::iteration<T, dims, dims> iter_type;
	public:
		/**
			The type of element in the index array.
		 */
		typedef T index_type;

		/**
			The type of the index array
		  */
		typedef typename detail::iteration<T, dims, dims>::index_array index_array;

		/**
			Advance the iteration one step
		  */
		inline multi_iteration<T,dims>& operator++() { if(this->advance()) finished=true; return *this; }

		/**
			Returns true iff the iteration is still going (the index has a legal value)
		  */
		inline operator bool () const { return !finished; }

		/**
			Returns the index array.
		  */
		inline index_array& operator*() { return this->index(); }

		/**
			Construct a multi_iteration with the given extent.
		  */
		inline multi_iteration(const initializer_list<T>& ext) :
			iter_type(ext), finished(false) { }


		inline multi_iteration(const std::array<T,dims>& ext) :
			iter_type(ext), finished(false) { }

	};


	
	

	


} // end namespace vectorl

#endif
